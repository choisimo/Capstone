"""
Gemini AI 응답 파서
"""
import re
import json
import orjson
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from .base_parser import BaseParser, ParseResult, ValidationError
import logging

logger = logging.getLogger(__name__)


class GeminiResponseSchema(BaseModel):
    """Gemini 응답 스키마"""
    raw_response: str
    parsed_data: Optional[Dict[str, Any]] = None
    response_type: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """신뢰도 검증"""
        return max(0.0, min(1.0, v))


class GeminiResponseParser(BaseParser):
    """
    Gemini AI 응답 전용 파서
    
    Gemini 모델의 특성을 고려한 최적화된 파싱
    """
    
    def __init__(self):
        super().__init__()
        self.response_patterns = {
            'sentiment': self._parse_sentiment_response,
            'absa': self._parse_absa_response,
            'news_analysis': self._parse_news_response,
            'structure_learning': self._parse_structure_response,
            'change_analysis': self._parse_change_response,
            'pension_sentiment': self._parse_pension_response,
            'keywords': self._parse_keywords_response,
            'summary': self._parse_summary_response
        }
    
    def parse(self, response: str, response_type: str = "auto", **kwargs) -> ParseResult:
        """
        Gemini 응답 파싱
        
        Args:
            response: Gemini API 응답 문자열
            response_type: 응답 타입
            **kwargs: 추가 파라미터
        
        Returns:
            ParseResult 객체
        """
        try:
            # 응답 타입 자동 감지
            if response_type == "auto":
                response_type = self._detect_response_type(response)
            
            # JSON 추출 시도
            json_data = self.extract_json(response)
            
            if json_data:
                # 타입별 전용 파서 사용
                if response_type in self.response_patterns:
                    parsed_data = self.response_patterns[response_type](json_data)
                else:
                    parsed_data = self.normalize_data(json_data)
                
                # 검증
                if self.validate(parsed_data):
                    self.update_statistics(True)
                    return ParseResult(
                        success=True,
                        data=parsed_data,
                        metadata={
                            "response_type": response_type,
                            "confidence": self._calculate_confidence(parsed_data)
                        }
                    )
                else:
                    warnings = ["Validation passed but some fields may be incomplete"]
                    return ParseResult(
                        success=True,
                        data=parsed_data,
                        warnings=warnings,
                        metadata={"response_type": response_type}
                    )
            else:
                # JSON 추출 실패 시 텍스트 파싱
                parsed_data = self._fallback_parse(response, response_type)
                if parsed_data:
                    self.update_statistics(True)
                    return ParseResult(
                        success=True,
                        data=parsed_data,
                        warnings=["Fallback parsing used"],
                        metadata={"response_type": response_type}
                    )
            
            # 파싱 실패
            self.update_statistics(False)
            return ParseResult(
                success=False,
                errors=[f"Failed to parse {response_type} response"],
                metadata={"raw_response": response[:500]}
            )
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            self.update_statistics(False)
            return ParseResult(
                success=False,
                errors=[str(e)],
                metadata={"exception": type(e).__name__}
            )
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        if not data:
            return False
        
        # 필수 필드가 있는지 확인
        if len(data) == 0:
            return False
        
        # None이 아닌 값이 하나 이상 있는지 확인
        non_null_values = [v for v in data.values() if v is not None]
        
        return len(non_null_values) > 0
    
    def _detect_response_type(self, response: str) -> str:
        """
        응답 타입 자동 감지
        
        Args:
            response: 응답 텍스트
        
        Returns:
            감지된 응답 타입
        """
        type_indicators = {
            'sentiment': ['sentiment', 'emotion', 'positive', 'negative'],
            'absa': ['aspect', 'aspects'],
            'news_analysis': ['headline', 'stakeholder', 'news'],
            'structure_learning': ['css_selector', 'xpath', 'extraction'],
            'change_analysis': ['change', 'diff', 'modification'],
            'pension_sentiment': ['pension', 'retirement', '연금'],
            'keywords': ['keyword', 'entity', 'topic'],
            'summary': ['summary', 'key_point', '요약']
        }
        
        response_lower = response.lower()
        
        for response_type, indicators in type_indicators.items():
            if any(indicator in response_lower for indicator in indicators):
                return response_type
        
        return "unknown"
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        파싱 신뢰도 계산
        
        Args:
            data: 파싱된 데이터
        
        Returns:
            신뢰도 점수 (0.0 ~ 1.0)
        """
        if not data:
            return 0.0
        
        # 신뢰도 계산 요소
        factors = []
        
        # 1. 데이터 완성도
        total_fields = len(data)
        non_null_fields = sum(1 for v in data.values() if v not in [None, "", [], {}])
        if total_fields > 0:
            completeness = non_null_fields / total_fields
            factors.append(completeness)
        
        # 2. confidence 필드가 있으면 사용
        if 'confidence' in data:
            try:
                conf_value = float(data['confidence'])
                factors.append(conf_value)
            except (TypeError, ValueError):
                pass
        
        # 3. score 필드들의 유효성
        score_fields = [k for k in data.keys() if 'score' in k.lower()]
        for field in score_fields:
            try:
                score = float(data[field])
                if -1.0 <= score <= 1.0:
                    factors.append(1.0)
                else:
                    factors.append(0.5)
            except (TypeError, ValueError):
                factors.append(0.0)
        
        # 평균 계산
        if factors:
            return sum(factors) / len(factors)
        
        return 0.5  # 기본값
    
    def _parse_sentiment_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """감성 분석 응답 파싱"""
        parsed = {
            "overall_sentiment": data.get("overall_sentiment", "neutral"),
            "sentiment_score": self._safe_float(data.get("sentiment_score"), 0.0),
            "confidence": self._safe_float(data.get("confidence"), 0.0),
            "emotions": data.get("emotions", []),
            "explanation": data.get("explanation", ""),
            "key_phrases": data.get("key_phrases", [])
        }
        
        # 감성 점수 범위 확인
        parsed["sentiment_score"] = max(-1.0, min(1.0, parsed["sentiment_score"]))
        
        return parsed
    
    def _parse_absa_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ABSA 응답 파싱"""
        aspects = data.get("aspects", [])
        
        # 각 aspect 정규화
        normalized_aspects = []
        for aspect in aspects:
            if isinstance(aspect, dict):
                normalized = {
                    "aspect": aspect.get("aspect", ""),
                    "sentiment": aspect.get("sentiment", "neutral"),
                    "score": self._safe_float(aspect.get("score"), 0.0),
                    "confidence": self._safe_float(aspect.get("confidence"), 0.0),
                    "mentions": aspect.get("mentions", []),
                    "keywords": aspect.get("keywords", [])
                }
                normalized_aspects.append(normalized)
        
        return {
            "aspects": normalized_aspects,
            "main_topics": data.get("main_topics", []),
            "overall_summary": data.get("overall_summary", "")
        }
    
    def _parse_news_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 분석 응답 파싱"""
        return {
            "headline_sentiment": data.get("headline_sentiment", "neutral"),
            "content_summary": data.get("content_summary", ""),
            "stakeholders": data.get("stakeholders", []),
            "impact_assessment": data.get("impact_assessment", {}),
            "credibility_score": self._safe_float(data.get("credibility_score"), 0.0),
            "bias_detection": data.get("bias_detection", {}),
            "related_topics": data.get("related_topics", [])
        }
    
    def _parse_structure_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """구조 학습 응답 파싱"""
        structure = data.get("structure", {})
        
        # 각 필드의 selector 정보 정규화
        normalized_structure = {}
        for field, selectors in structure.items():
            if isinstance(selectors, dict):
                normalized_structure[field] = {
                    "css_selector": selectors.get("css_selector", ""),
                    "xpath": selectors.get("xpath", ""),
                    "confidence": self._safe_float(selectors.get("confidence"), 0.0)
                }
            elif isinstance(selectors, str):
                normalized_structure[field] = {
                    "css_selector": selectors,
                    "xpath": "",
                    "confidence": 0.5
                }
        
        return {
            "structure": normalized_structure,
            "page_type": data.get("page_type", "unknown"),
            "confidence": self._safe_float(data.get("confidence"), 0.0),
            "extraction_hints": data.get("extraction_hints", [])
        }
    
    def _parse_change_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """변경 분석 응답 파싱"""
        return {
            "change_type": data.get("change_type", "unknown"),
            "importance_score": self._safe_int(data.get("importance_score"), 0),
            "sentiment_shift": self._safe_float(data.get("sentiment_shift"), 0.0),
            "key_changes": data.get("key_changes", []),
            "notification_required": data.get("notification_required", False),
            "urgency": data.get("urgency", "low")
        }
    
    def _parse_pension_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """연금 감성 응답 파싱"""
        pension_sentiment = data.get("pension_sentiment", {})
        
        return {
            "pension_sentiment": {
                "trust_level": pension_sentiment.get("trust_level", "medium"),
                "satisfaction": self._safe_float(pension_sentiment.get("satisfaction"), 0.0),
                "reform_stance": pension_sentiment.get("reform_stance", "neutral"),
                "anxiety_level": self._safe_float(pension_sentiment.get("anxiety_level"), 0.5)
            },
            "key_concerns": data.get("key_concerns", []),
            "suggestions": data.get("suggestions", []),
            "demographic_hints": data.get("demographic_hints", {}),
            "sentiment_drivers": data.get("sentiment_drivers", []),
            "policy_implications": data.get("policy_implications", "")
        }
    
    def _parse_keywords_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """키워드 추출 응답 파싱"""
        return {
            "keywords": data.get("keywords", []),
            "entities": data.get("entities", {}),
            "topics": data.get("topics", [])
        }
    
    def _parse_summary_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """요약 응답 파싱"""
        return {
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "main_theme": data.get("main_theme", "")
        }
    
    def _fallback_parse(self, response: str, response_type: str) -> Optional[Dict[str, Any]]:
        """
        JSON 파싱 실패 시 폴백 파싱
        
        Args:
            response: 응답 텍스트
            response_type: 응답 타입
        
        Returns:
            파싱된 데이터 또는 None
        """
        # 키-값 쌍 추출 시도
        kv_pairs = self.extract_key_value_pairs(response)
        if kv_pairs:
            return kv_pairs
        
        # 리스트 추출 시도
        list_pattern = r"[-•*]\s*(.+)"
        matches = re.findall(list_pattern, response)
        if matches:
            return {"items": matches}
        
        # 텍스트만 반환
        if response.strip():
            return {"raw_text": response.strip()}
        
        return None
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """안전한 float 변환"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """안전한 int 변환"""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
