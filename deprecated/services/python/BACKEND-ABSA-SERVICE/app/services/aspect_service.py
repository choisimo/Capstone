"""
Aspect Service 모듈

속성 관리 및 추출을 위한 서비스입니다.
"""

from typing import List, Dict, Any, Optional
import uuid
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
        
        # 텍스트 기반 결정론적 추출: 텍스트에 등장하는 후보를 우선 선택
        lowered = text.lower()
        appearances: List[Dict[str, Any]] = []
        for asp in candidate_aspects:
            idx = lowered.find(asp.lower())
            if idx != -1:
                appearances.append({"aspect": asp, "index": idx})

        # 기본 개수: 텍스트 길이에 따라 1~4개 범위에서 결정(결정론적)
        word_count = len(lowered.split())
        desired_count = max(1, min(4, word_count // 10 + 1))

        # 우선순위: 등장 순서 -> 알파벳
        if appearances:
            appearances.sort(key=lambda x: (x["index"], x["aspect"]))
            selected = [a["aspect"] for a in appearances[:desired_count]]
        else:
            # 등장하지 않으면 후보 리스트 앞에서 deterministic 선택
            selected = candidate_aspects[:desired_count]

        for aspect in selected:
            pos = lowered.find(aspect.lower())
            if pos == -1:
                pos = 0
            end_pos = min(len(text), pos + max(10, len(aspect)))
            # 신뢰도: 단어 길이/텍스트 길이 기반 (0.6~0.95 범위로 정규화)
            base = len(aspect) / max(10.0, len(text))
            confidence = 0.6 + min(0.35, base * 5.0)

            aspect_data = {
                "aspect": aspect,
                "confidence": round(confidence, 2),
                "position": {
                    "start": pos,
                    "end": end_pos
                },
                "context": text[max(0, pos-25):min(len(text), end_pos+25)] if text else ""
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