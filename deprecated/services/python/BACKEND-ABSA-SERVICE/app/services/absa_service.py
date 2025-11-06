"""
ABSA Service 서비스 모듈

속성 기반 감성 분석의 핵심 비즈니스 로직을 담당합니다.
실제 텍스트 분석과 감성 점수 계산을 수행합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import uuid
import re
import numpy as np
from datetime import datetime
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ABSAService:
    """속성 기반 감성 분석 서비스"""
    
    def __init__(self):
        self.model_cache = {}
        self.sentiment_lexicon = self._load_sentiment_lexicon()
        self.aspect_keywords = self._load_aspect_keywords()
        
    def _load_sentiment_lexicon(self) -> Dict[str, float]:
        """감성 사전 로드"""
        # 한국어 감성 단어 사전 (실제로는 외부 파일에서 로드)
        return {
            # 긍정 단어
            "좋은": 0.8, "훌륭한": 0.9, "최고": 1.0, "만족": 0.7,
            "개선": 0.6, "향상": 0.6, "안정": 0.7, "믿음": 0.8,
            "신뢰": 0.8, "효율적": 0.7, "편리한": 0.6, "유익한": 0.7,
            "긍정적": 0.8, "희망": 0.7, "성공": 0.8, "발전": 0.7,
            
            # 부정 단어  
            "나쁜": -0.8, "최악": -1.0, "불만": -0.7, "걱정": -0.6,
            "우려": -0.6, "불안": -0.7, "위험": -0.8, "문제": -0.5,
            "실패": -0.8, "부족": -0.6, "비효율": -0.7, "불편": -0.6,
            "부정적": -0.8, "절망": -0.9, "악화": -0.8, "퇴보": -0.7,
            
            # 중립/약한 감성
            "보통": 0.0, "평범": 0.0, "일반": 0.0, "그저": -0.1,
            "적당": 0.1, "무난": 0.1, "괜찮": 0.3, "나름": 0.2
        }
    
    def _load_aspect_keywords(self) -> Dict[str, List[str]]:
        """속성별 키워드 사전 로드"""
        return {
            "수익률": ["수익", "이익", "손실", "수익률", "투자", "운용", "성과"],
            "안정성": ["안정", "안전", "위험", "보장", "확실", "지속", "유지"],
            "관리비용": ["비용", "수수료", "관리비", "운용비", "경비", "지출"],
            "가입조건": ["가입", "자격", "조건", "요건", "기준", "대상", "연령"],
            "급여수준": ["급여", "연금", "수령", "지급", "금액", "혜택", "보장"],
            "제도개선": ["개혁", "개선", "변경", "수정", "보완", "강화", "완화"],
            "신뢰도": ["신뢰", "믿음", "투명", "공정", "정직", "책임", "의심"],
            "미래전망": ["미래", "전망", "예측", "장기", "지속", "발전", "성장"]
        }
    
    async def analyze_text(
        self, 
        text: str, 
        aspects: List[str], 
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        텍스트에 대한 속성별 감성 분석 수행
        
        Args:
            text: 분석할 텍스트
            aspects: 분석할 속성 리스트
            model_name: 사용할 모델명 (기본값: None)
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # 전체 감성 점수 계산
            overall_sentiment, overall_confidence = self._calculate_overall_sentiment(processed_text)
            
            # 속성별 분석
            aspect_results = []
            for aspect in aspects:
                aspect_sentiment, confidence, relevance = self._analyze_aspect(
                    processed_text, aspect
                )
                aspect_results.append({
                    "aspect": aspect,
                    "sentiment": aspect_sentiment,
                    "sentiment_score": self._sentiment_to_score(aspect_sentiment),
                    "confidence": confidence,
                    "relevance": relevance,
                    "keywords_found": self._find_aspect_keywords(processed_text, aspect)
                })
            
            results = {
                "text": text,
                "aspects": aspect_results,
                "overall_sentiment": overall_sentiment,
                "overall_score": self._sentiment_to_score(overall_sentiment),
                "confidence": overall_confidence,
                "analysis_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "model": model_name or "rule-based-v1"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_text: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 소문자 변환 (영어의 경우)
        text = text.lower()
        
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 중복 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _calculate_overall_sentiment(self, text: str) -> Tuple[str, float]:
        """전체 텍스트의 감성 점수 계산"""
        words = text.split()
        sentiment_scores = []
        
        for word in words:
            if word in self.sentiment_lexicon:
                sentiment_scores.append(self.sentiment_lexicon[word])
        
        if not sentiment_scores:
            return "neutral", 0.5
        
        avg_score = np.mean(sentiment_scores)
        confidence = min(0.95, 0.5 + abs(avg_score) * 0.5)
        
        if avg_score > 0.3:
            return "positive", confidence
        elif avg_score < -0.3:
            return "negative", confidence
        else:
            return "neutral", confidence
    
    def _analyze_aspect(self, text: str, aspect: str) -> Tuple[str, float, float]:
        """특정 속성에 대한 감성 분석"""
        # 속성 관련 키워드 찾기
        keywords = self.aspect_keywords.get(aspect, [])
        found_keywords = []
        
        for keyword in keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        if not found_keywords:
            # 속성과 관련 없는 경우
            return "neutral", 0.3, 0.1
        
        # 속성 관련 문맥에서 감성 분석
        aspect_sentiment_scores = []
        words = text.split()
        
        for i, word in enumerate(words):
            if any(kw in word for kw in found_keywords):
                # 주변 단어들의 감성 점수 확인 (앞뒤 3단어)
                context_start = max(0, i - 3)
                context_end = min(len(words), i + 4)
                
                for j in range(context_start, context_end):
                    if words[j] in self.sentiment_lexicon:
                        # 거리에 따른 가중치 적용
                        distance = abs(j - i)
                        weight = 1.0 / (1 + distance * 0.3)
                        aspect_sentiment_scores.append(
                            self.sentiment_lexicon[words[j]] * weight
                        )
        
        if not aspect_sentiment_scores:
            return "neutral", 0.5, len(found_keywords) / len(keywords)
        
        avg_score = np.mean(aspect_sentiment_scores)
        relevance = min(1.0, len(found_keywords) / max(1, len(keywords)))
        confidence = min(0.9, 0.5 + relevance * 0.4)
        
        if avg_score > 0.3:
            return "positive", confidence, relevance
        elif avg_score < -0.3:
            return "negative", confidence, relevance
        else:
            return "neutral", confidence, relevance
    
    def _find_aspect_keywords(self, text: str, aspect: str) -> List[str]:
        """텍스트에서 속성 관련 키워드 찾기"""
        keywords = self.aspect_keywords.get(aspect, [])
        found = []
        
        for keyword in keywords:
            if keyword in text:
                found.append(keyword)
        
        return found
    
    def _sentiment_to_score(self, sentiment: str) -> float:
        """감성 레이블을 점수로 변환"""
        mapping = {
            "positive": 1.0,
            "neutral": 0.0,
            "negative": -1.0
        }
        return mapping.get(sentiment, 0.0)
    
    async def bulk_analyze(
        self, 
        texts: List[str], 
        aspects: List[str]
    ) -> List[Dict[str, Any]]:
        """
        여러 텍스트에 대한 일괄 분석
        
        Args:
            texts: 분석할 텍스트 리스트
            aspects: 분석할 속성 리스트
            
        Returns:
            분석 결과 리스트
        """
        results = []
        
        for text in texts:
            result = await self.analyze_text(text, aspects)
            results.append(result)
        
        return results
    
    async def get_aspect_insights(
        self, 
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        분석 결과로부터 속성별 인사이트 추출
        
        Args:
            analysis_results: 분석 결과 리스트
            
        Returns:
            속성별 인사이트
        """
        insights = {
            "total_analyzed": len(analysis_results),
            "aspect_summary": {},
            "overall_trends": {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # 속성별 감성 분포 계산
        aspect_counts = {}
        for result in analysis_results:
            for aspect_data in result.get("aspects", []):
                aspect = aspect_data["aspect"]
                sentiment = aspect_data["sentiment"]
                
                if aspect not in aspect_counts:
                    aspect_counts[aspect] = {"positive": 0, "negative": 0, "neutral": 0}
                
                aspect_counts[aspect][sentiment] += 1
        
        insights["aspect_summary"] = aspect_counts
        
        return insights