"""
Aspect Service 모듈

속성 관리 및 추출을 위한 서비스입니다.
"""

from typing import List, Dict, Any, Optional
import uuid
import random
from datetime import datetime


class AspectService:
    """속성 관리 서비스"""
    
    def __init__(self):
        # 미리 정의된 속성 카테고리
        self.predefined_aspects = {
            "pension": ["contribution", "benefit", "retirement_age", "investment", "security"],
            "finance": ["cost", "fee", "return", "risk", "liquidity"],
            "service": ["customer_service", "accessibility", "transparency", "speed", "reliability"]
        }
    
    async def extract_aspects(
        self, 
        text: str, 
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트에서 속성 추출
        
        Args:
            text: 분석할 텍스트
            domain: 도메인 카테고리 (pension, finance, service 등)
            
        Returns:
            추출된 속성 리스트
        """
        # 실제 NLP 모델 대신 임시 구현
        extracted_aspects = []
        
        # 도메인별 속성 선택
        if domain and domain in self.predefined_aspects:
            candidate_aspects = self.predefined_aspects[domain]
        else:
            # 모든 속성을 후보로 설정
            candidate_aspects = []
            for aspects in self.predefined_aspects.values():
                candidate_aspects.extend(aspects)
        
        # 텍스트 길이에 따라 속성 개수 결정
        text_length = len(text.split())
        num_aspects = min(random.randint(1, 4), text_length // 10 + 1)
        
        selected_aspects = random.sample(
            candidate_aspects, 
            min(num_aspects, len(candidate_aspects))
        )
        
        for aspect in selected_aspects:
            aspect_data = {
                "aspect": aspect,
                "confidence": round(random.uniform(0.6, 0.95), 2),
                "position": {
                    "start": random.randint(0, max(0, len(text) - 10)),
                    "end": random.randint(10, len(text))
                },
                "context": text[:50] + "..." if len(text) > 50 else text
            }
            extracted_aspects.append(aspect_data)
        
        return extracted_aspects
    
    async def get_aspect_suggestions(
        self, 
        domain: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        도메인별 추천 속성 반환
        
        Args:
            domain: 특정 도메인 (None이면 전체)
            
        Returns:
            도메인별 속성 딕셔너리
        """
        if domain and domain in self.predefined_aspects:
            return {domain: self.predefined_aspects[domain]}
        
        return self.predefined_aspects
    
    async def validate_aspects(
        self, 
        aspects: List[str], 
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        입력된 속성들의 유효성 검증
        
        Args:
            aspects: 검증할 속성 리스트
            domain: 도메인 카테고리
            
        Returns:
            검증 결과
        """
        validation_result = {
            "valid_aspects": [],
            "invalid_aspects": [],
            "suggestions": [],
            "domain": domain
        }
        
        # 유효한 속성 목록 생성
        valid_aspects = []
        if domain and domain in self.predefined_aspects:
            valid_aspects = self.predefined_aspects[domain]
        else:
            for aspects_list in self.predefined_aspects.values():
                valid_aspects.extend(aspects_list)
        
        for aspect in aspects:
            if aspect.lower() in [v.lower() for v in valid_aspects]:
                validation_result["valid_aspects"].append(aspect)
            else:
                validation_result["invalid_aspects"].append(aspect)
                # 유사한 속성 제안
                similar_aspects = [
                    v for v in valid_aspects 
                    if aspect.lower() in v.lower() or v.lower() in aspect.lower()
                ]
                validation_result["suggestions"].extend(similar_aspects[:3])
        
        return validation_result
    
    async def get_aspect_trends(
        self, 
        analysis_history: List[Dict[str, Any]], 
        time_range: str = "7d"
    ) -> Dict[str, Any]:
        """
        속성별 트렌드 분석
        
        Args:
            analysis_history: 분석 이력 데이터
            time_range: 분석 기간 (7d, 30d, 90d)
            
        Returns:
            트렌드 분석 결과
        """
        trends = {
            "time_range": time_range,
            "aspect_frequency": {},
            "sentiment_trends": {},
            "emerging_aspects": [],
            "declining_aspects": [],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # 속성 빈도 계산
        aspect_counts = {}
        for analysis in analysis_history:
            for aspect_data in analysis.get("aspects", []):
                aspect = aspect_data["aspect"]
                aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
        
        trends["aspect_frequency"] = dict(
            sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
        )
        
        # 상위 5개 속성을 emerging으로, 하위 3개를 declining으로 설정 (임시)
        if aspect_counts:
            sorted_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
            trends["emerging_aspects"] = [asp[0] for asp in sorted_aspects[:5]]
            trends["declining_aspects"] = [asp[0] for asp in sorted_aspects[-3:]]
        
        return trends