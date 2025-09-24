"""
Gemini AI 클라이언트 구현 v2.0
하이브리드 지능형 크롤링 시스템을 위한 개선된 버전
"""
from __future__ import annotations
import os
import json
import re
import asyncio
import aiohttp
import orjson
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from pydantic import BaseModel, Field, validator
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiModel(Enum):
    """사용 가능한 Gemini 모델 및 특성"""
    FLASH_15 = "gemini-1.5-flash"  # 빠르고 비용 효율적
    PRO_15 = "gemini-1.5-pro"       # 높은 정확도
    PRO_VISION = "gemini-pro-vision"  # 비전 기능


class SafetySettings:
    """Gemini API 안전 설정"""
    DEFAULT = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    content: str
    prompt_type: str = "sentiment"
    model_name: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, le=8192)
    additional_context: Optional[str] = None


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    status: str
    model: str
    timestamp: str
    data: Dict[str, Any]
    error: Optional[str] = None


class GeminiClientV2:
    """
    개선된 Gemini AI 클라이언트
    
    특징:
    - 비동기 처리 지원
    - 강화된 재시도 로직
    - 구조화된 데이터 모델
    - 확장된 프롬프트 템플릿
    - 멀티모델 지원
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        클라이언트 초기화
        
        Args:
            api_key: Gemini API 키 (환경변수 GEMINI_API_KEY로도 설정 가능)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key)
        
        # 모델 초기화
        self.models = {
            GeminiModel.FLASH_15.value: genai.GenerativeModel(GeminiModel.FLASH_15.value),
            GeminiModel.PRO_15.value: genai.GenerativeModel(GeminiModel.PRO_15.value),
            GeminiModel.PRO_VISION.value: genai.GenerativeModel(GeminiModel.PRO_VISION.value)
        }
        
        self.default_model = GeminiModel.FLASH_15.value
        self.safety_settings = SafetySettings.DEFAULT
        
        # 비동기 세션
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"GeminiClientV2 initialized with default model: {self.default_model}")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._session:
            await self._session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def analyze_content(
        self,
        content: str,
        prompt_type: str = "sentiment",
        model_name: Optional[str] = None,
        **kwargs
    ) -> AnalysisResponse:
        """
        콘텐츠 분석 메인 메서드
        
        Args:
            content: 분석할 텍스트
            prompt_type: 분석 유형
            model_name: 사용할 모델
            **kwargs: 추가 파라미터
        
        Returns:
            AnalysisResponse 객체
        """
        try:
            # 요청 검증
            request = AnalysisRequest(
                content=content,
                prompt_type=prompt_type,
                model_name=model_name,
                **kwargs
            )
            
            # 모델 선택
            model = self.models.get(request.model_name or self.default_model)
            if not model:
                model = self.models[self.default_model]
            
            # 프롬프트 생성
            prompt = self._get_prompt(request.content, request.prompt_type, request.additional_context)
            
            # API 호출
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.GenerationConfig(
                    temperature=request.temperature,
                    top_p=kwargs.get('top_p', 0.95),
                    top_k=kwargs.get('top_k', 40),
                    max_output_tokens=request.max_tokens,
                )
            )
            
            # 응답 파싱
            result = self._parse_response(response.text, request.prompt_type)
            
            return AnalysisResponse(
                status="success",
                model=request.model_name or self.default_model,
                timestamp=datetime.utcnow().isoformat(),
                data=result
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return AnalysisResponse(
                status="error",
                model=model_name or self.default_model,
                timestamp=datetime.utcnow().isoformat(),
                data={},
                error=str(e)
            )
    
    def _get_prompt(self, content: str, prompt_type: str, additional_context: Optional[str] = None) -> str:
        """프롬프트 타입별 템플릿 반환"""
        prompt_templates = {
            "sentiment": self._get_sentiment_prompt,
            "summary": self._get_summary_prompt,
            "keywords": self._get_keywords_prompt,
            "absa": self._get_absa_prompt,
            "news_analysis": self._get_news_analysis_prompt,
            "pension_sentiment": self._get_pension_sentiment_prompt,
            "structure_learning": self._get_structure_learning_prompt,
            "change_analysis": self._get_change_analysis_prompt,
        }
        
        template_func = prompt_templates.get(prompt_type)
        if not template_func:
            logger.warning(f"Unknown prompt type: {prompt_type}, using default")
            return content
        
        return template_func(content, additional_context)
    
    def _get_sentiment_prompt(self, content: str, context: Optional[str] = None) -> str:
        """감성 분석 프롬프트"""
        context_text = f"\n맥락: {context}" if context else ""
        
        return f"""
        다음 텍스트의 감성을 분석해주세요.{context_text}
        
        텍스트: {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "overall_sentiment": "positive/negative/neutral",
            "sentiment_score": -1.0 ~ 1.0 사이의 숫자,
            "confidence": 0.0 ~ 1.0 사이의 숫자,
            "emotions": ["주요 감정1", "주요 감정2"],
            "explanation": "간단한 설명"
        }}
        """
    
    def _get_summary_prompt(self, content: str, context: Optional[str] = None) -> str:
        """요약 프롬프트"""
        return f"""
        다음 텍스트를 핵심 내용 중심으로 요약해주세요.
        
        텍스트: {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "summary": "3-5문장 요약",
            "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
            "main_theme": "주요 주제"
        }}
        """
    
    def _get_keywords_prompt(self, content: str, context: Optional[str] = None) -> str:
        """키워드 추출 프롬프트"""
        return f"""
        다음 텍스트에서 중요한 키워드를 추출해주세요.
        
        텍스트: {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "keywords": ["키워드1", "키워드2", "..."],
            "entities": {{
                "people": ["인물"],
                "organizations": ["조직"],
                "locations": ["장소"],
                "dates": ["날짜"],
                "money": ["금액"]
            }},
            "topics": ["주제1", "주제2"]
        }}
        """
    
    def _get_absa_prompt(self, content: str, context: Optional[str] = None) -> str:
        """Aspect-Based Sentiment Analysis 프롬프트"""
        return f"""
        다음 텍스트에서 aspect별 감성을 분석해주세요.
        특히 연금, 금융, 정책 관련 aspect에 주목해주세요.
        
        텍스트: {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "aspects": [
                {{
                    "aspect": "aspect 이름",
                    "sentiment": "positive/negative/neutral",
                    "score": -1.0 ~ 1.0,
                    "mentions": ["관련 문장이나 구절"],
                    "keywords": ["관련 키워드"]
                }}
            ],
            "main_topics": ["주요 토픽1", "주요 토픽2"],
            "overall_summary": "전체 요약"
        }}
        """
    
    def _get_pension_sentiment_prompt(self, content: str, context: Optional[str] = None) -> str:
        """연금 관련 감성 분석 전문 프롬프트"""
        return f"""
        다음 텍스트에서 연금 관련 감성과 의견을 상세히 분석해주세요.
        
        텍스트: {content}
        
        분석 관점:
        1. 국민연금에 대한 감성 (신뢰도, 만족도)
        2. 연금개혁에 대한 입장
        3. 노후 준비에 대한 불안감
        4. 세대별 관점 차이
        5. 정책 제안이나 개선 요구사항
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "pension_sentiment": {{
                "trust_level": "high/medium/low",
                "satisfaction": -1.0 ~ 1.0,
                "reform_stance": "supportive/opposed/neutral",
                "anxiety_level": 0.0 ~ 1.0
            }},
            "key_concerns": ["주요 우려사항 리스트"],
            "suggestions": ["제안사항 리스트"],
            "demographic_hints": {{
                "age_group": "추정 연령대",
                "perspective": "관점 설명"
            }},
            "sentiment_drivers": ["감성을 유발한 주요 요인"],
            "policy_implications": "정책적 시사점"
        }}
        """
    
    def _get_news_analysis_prompt(self, content: str, context: Optional[str] = None) -> str:
        """뉴스 분석 종합 프롬프트"""
        return f"""
        다음 뉴스 기사를 종합적으로 분석해주세요.
        
        기사 내용: {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "headline_sentiment": "positive/negative/neutral",
            "content_summary": "핵심 내용 요약",
            "stakeholders": ["이해관계자 리스트"],
            "impact_assessment": {{
                "short_term": "단기 영향",
                "long_term": "장기 영향",
                "affected_groups": ["영향받는 그룹"]
            }},
            "public_sentiment_prediction": "예상되는 대중 반응",
            "credibility_score": 0.0 ~ 1.0,
            "bias_detection": {{
                "detected": true/false,
                "type": "bias 유형",
                "explanation": "설명"
            }},
            "related_topics": ["관련 주제"],
            "follow_up_needed": true/false
        }}
        """
    
    def _get_structure_learning_prompt(self, content: str, context: Optional[str] = None) -> str:
        """웹 구조 학습 프롬프트"""
        return f"""
        다음 HTML 구조를 분석하여 데이터 추출 템플릿을 생성해주세요.
        
        HTML: {content[:3000]}
        
        다음 정보를 추출하기 위한 CSS 셀렉터 또는 XPath를 찾아주세요:
        - 제목 (title)
        - 본문 (content)
        - 작성일 (date)
        - 저자 (author)
        - 카테고리 (category)
        - 태그 (tags)
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "structure": {{
                "title": "CSS selector or XPath",
                "content": "CSS selector or XPath",
                "date": "CSS selector or XPath",
                "author": "CSS selector or XPath",
                "category": "CSS selector or XPath",
                "tags": "CSS selector or XPath"
            }},
            "confidence": 0.0 ~ 1.0,
            "page_type": "news/blog/forum/etc",
            "extraction_hints": ["추출 힌트"],
            "potential_issues": ["잠재적 문제점"]
        }}
        """
    
    def _get_change_analysis_prompt(self, content: str, context: Optional[str] = None) -> str:
        """변경사항 분석 프롬프트"""
        # context should contain before and after content
        return f"""
        웹페이지 변경사항을 분석해주세요.
        
        {content}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "change_type": "major/minor/cosmetic",
            "importance_score": 1-10,
            "change_summary": "변경사항 요약",
            "sentiment_shift": -1.0 ~ 1.0,
            "key_changes": ["주요 변경사항 리스트"],
            "notification_required": true/false,
            "urgency": "high/medium/low",
            "affected_aspects": ["영향받는 측면들"]
        }}
        """
    
    def _parse_response(self, response_text: str, prompt_type: str) -> Dict[str, Any]:
        """
        Gemini 응답 파싱
        
        Args:
            response_text: Gemini 응답 텍스트
            prompt_type: 프롬프트 타입
        
        Returns:
            파싱된 결과 딕셔너리
        """
        try:
            # Try parsing with orjson (faster)
            try:
                return orjson.loads(response_text)
            except:
                pass
            
            # Extract JSON from markdown blocks
            json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
            match = re.search(json_pattern, response_text, re.IGNORECASE)
            if match:
                return orjson.loads(match.group(1))
            
            # Find JSON object in text
            json_obj_pattern = r"\{[\s\S]*\}"
            match = re.search(json_obj_pattern, response_text)
            if match:
                return orjson.loads(match.group(0))
            
            raise ValueError("Failed to parse JSON from response")
            
        except Exception as e:
            logger.error(f"Parse error for {prompt_type}: {e}")
            # Return structured error response
            return {
                "parse_error": True,
                "raw_response": response_text[:500],
                "error_message": str(e),
                "prompt_type": prompt_type
            }
    
    async def analyze_web_content(
        self,
        url: str,
        html_content: str,
        extraction_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        웹 콘텐츠 구조화 데이터 추출
        
        Args:
            url: 웹페이지 URL
            html_content: HTML 콘텐츠
            extraction_prompt: 커스텀 추출 프롬프트
        
        Returns:
            구조화된 데이터
        """
        prompt = extraction_prompt or self._get_structure_learning_prompt(html_content)
        
        return await self.analyze_content(
            prompt,
            prompt_type="structure_learning",
            additional_context=f"URL: {url}"
        )
    
    async def batch_analyze(
        self,
        contents: List[str],
        prompt_type: str = "sentiment",
        batch_size: int = 5
    ) -> List[AnalysisResponse]:
        """
        배치 분석 처리
        
        Args:
            contents: 분석할 콘텐츠 리스트
            prompt_type: 분석 타입
            batch_size: 동시 처리 배치 크기
        
        Returns:
            분석 결과 리스트
        """
        results = []
        
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i+batch_size]
            tasks = [
                self.analyze_content(content, prompt_type)
                for content in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis error: {result}")
                    results.append(AnalysisResponse(
                        status="error",
                        model=self.default_model,
                        timestamp=datetime.utcnow().isoformat(),
                        data={},
                        error=str(result)
                    ))
                else:
                    results.append(result)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        return results
    
    async def analyze_change(
        self,
        before_content: str,
        after_content: str
    ) -> Dict[str, Any]:
        """
        변경사항 분석
        
        Args:
            before_content: 이전 콘텐츠
            after_content: 현재 콘텐츠
        
        Returns:
            변경사항 분석 결과
        """
        context = f"""
        이전 내용:
        {before_content[:1000]}
        
        현재 내용:
        {after_content[:1000]}
        """
        
        response = await self.analyze_content(
            context,
            prompt_type="change_analysis"
        )
        
        return response.data if response.status == "success" else {}


# Backward compatibility
GeminiClient = GeminiClientV2
