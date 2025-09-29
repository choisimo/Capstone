"""
Aspect Service 모듈

속성 관리 및 추출을 위한 서비스입니다.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import re


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
        텍스트에서 속성 추출 (키워드 기반 실제 분석)
        
        Args:
            text: 분석할 텍스트
            domain: 도메인 카테고리 (pension, finance, service 등)
            
        Returns:
            추출된 속성 리스트
        """
        extracted_aspects = []
        
        # 도메인별 키워드 매핑 (실제 언급 기반)
        aspect_keywords = {
            "contribution": ["보험료", "기여", "납부", "부담"],
            "benefit": ["급여", "수령", "지급", "연금액"],
            "retirement_age": ["수령", "은퇴", "정년", "나이"],
            "investment": ["수익", "투자", "운용", "수익률"],
            "security": ["안정", "보장", "신뢰", "안전"],
            "cost": ["비용", "수수료", "경비"],
            "fee": ["수수료", "관리비", "비용"],
            "return": ["수익률", "이익", "수익"],
            "risk": ["위험", "리스크", "불안"],
            "liquidity": ["유동성", "환금"],
            "customer_service": ["서비스", "고객", "상담"],
            "accessibility": ["접근", "편의", "이용"],
            "transparency": ["투명", "공개", "명확"],
            "speed": ["신속", "빠른", "지연"],
            "reliability": ["신뢰", "믿음", "안정"]
        }
        
        # 도메인 필터링
        if domain and domain in self.predefined_aspects:
            candidate_aspects = self.predefined_aspects[domain]
        else:
            candidate_aspects = []
            for aspects in self.predefined_aspects.values():
                candidate_aspects.extend(aspects)
        
        # 텍스트에서 실제 언급된 속성만 추출
        text_lower = text.lower()
        for aspect in candidate_aspects:
            keywords = aspect_keywords.get(aspect, [])
            
            for keyword in keywords:
                # 키워드가 실제로 텍스트에 있는지 확인
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = list(pattern.finditer(text))
                
                if matches:
                    # 첫 번째 매치 위치 사용
                    match = matches[0]
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # 주변 컨텍스트 추출 (앞뒤 30자)
                    context_start = max(0, start_pos - 30)
                    context_end = min(len(text), end_pos + 30)
                    context = text[context_start:context_end]
                    
                    # 신뢰도는 매치 횟수와 위치에 기반
                    confidence = min(0.95, 0.6 + len(matches) * 0.1)
                    
                    aspect_data = {
                        "aspect": aspect,
                        "confidence": round(confidence, 2),
                        "position": {
                            "start": start_pos,
                            "end": end_pos
                        },
                        "context": context.strip(),
                        "keyword_matched": keyword,
                        "match_count": len(matches)
                    }
                    extracted_aspects.append(aspect_data)
                    break  # 한 aspect당 하나의 매치만
        
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