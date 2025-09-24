"""
연금 도메인 특화 프롬프트 템플릿
"""
from typing import Dict, Any, List
from .base import BasePromptTemplate


class PensionPromptTemplate(BasePromptTemplate):
    """연금 관련 종합 분석 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["pension", "retirement", "social-security", "comprehensive"]
        self.metadata.domain = "pension"
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 한국 국민연금 및 노후보장 정책 분석 전문가입니다.
        
전문 분야:
1. 국민연금 제도 및 정책 분석
2. 연금 개혁 방안 평가
3. 노후 소득 보장 체계 분석
4. 세대 간 부담 및 수혜 구조 평가
5. 연금 재정 지속가능성 분석
6. 국제 연금 제도 비교

분석 원칙:
- 객관적이고 균형잡힌 시각 유지
- 다양한 이해관계자 관점 고려
- 단기/장기 영향 구분
- 정량적 근거 중시
- 정책 대안 제시

핵심 고려사항:
- 인구 고령화 추세
- 저출산 영향
- 경제성장률 변화
- 노동시장 구조 변화
- 소득 양극화
- 세대 간 형평성

반드시 지정된 JSON 형식으로 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        analysis_focus = kwargs.get('focus', 'comprehensive')
        perspective = kwargs.get('perspective', 'neutral')  # neutral/citizen/expert/government
        
        prompt = f"""다음 연금 관련 텍스트를 종합적으로 분석해주세요.

분석 대상 텍스트:
{content}

분석 초점: {analysis_focus}
분석 관점: {perspective}

다음 사항들을 중점적으로 분석해주세요:
1. 국민연금에 대한 전반적인 감성과 신뢰도
2. 연금 개혁에 대한 입장과 논거
3. 노후 준비에 대한 인식과 우려사항
4. 세대별 관점의 차이점
5. 정책 제안이나 개선 요구사항
6. 잠재적 사회경제적 영향"""
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "pension_sentiment": {
                "trust_level": "high/medium/low",
                "satisfaction": "float (-1.0 ~ 1.0)",
                "reform_stance": "supportive/opposed/neutral/mixed",
                "anxiety_level": "float (0.0 ~ 1.0)"
            },
            "key_concerns": ["우려사항 리스트"],
            "suggestions": ["제안사항 리스트"],
            "demographic_hints": {
                "age_group": "20s/30s/40s/50s/60s+/unknown",
                "occupation": "추정 직업군",
                "income_level": "high/middle/low/unknown",
                "perspective": "관점 설명"
            },
            "sentiment_drivers": ["감성 유발 요인"],
            "policy_implications": "정책적 시사점",
            "reform_priorities": ["개혁 우선순위"],
            "stakeholder_impact": {
                "beneficiaries": ["수혜자 그룹"],
                "affected_negatively": ["부정적 영향 그룹"]
            },
            "sustainability_outlook": {
                "assessment": "positive/negative/uncertain",
                "key_factors": ["핵심 요인"],
                "timeline": "영향 시기"
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """예시 반환"""
        return [
            {
                "input": "30대 직장인입니다. 매달 국민연금 보험료를 내지만 정말 노후에 받을 수 있을지 의문입니다. 지금도 적자라는데 우리 세대가 은퇴할 때는 고갈될 것 같아 불안합니다.",
                "output": {
                    "pension_sentiment": {
                        "trust_level": "low",
                        "satisfaction": -0.7,
                        "reform_stance": "neutral",
                        "anxiety_level": 0.8
                    },
                    "key_concerns": [
                        "연금 고갈 우려",
                        "세대 간 불공정",
                        "미래 수급 불확실성"
                    ],
                    "suggestions": [],
                    "demographic_hints": {
                        "age_group": "30s",
                        "occupation": "직장인",
                        "income_level": "middle",
                        "perspective": "현 근로 세대의 불안감"
                    },
                    "sentiment_drivers": [
                        "연금 재정 적자 보도",
                        "미래 불확실성",
                        "세대 간 형평성 우려"
                    ],
                    "policy_implications": "젊은 세대의 신뢰 회복 필요",
                    "reform_priorities": ["재정 안정화", "투명성 제고"],
                    "stakeholder_impact": {
                        "beneficiaries": [],
                        "affected_negatively": ["30대 근로자"]
                    },
                    "sustainability_outlook": {
                        "assessment": "negative",
                        "key_factors": ["재정 적자", "신뢰도 하락"],
                        "timeline": "장기적"
                    }
                }
            }
        ]


class PensionReformPromptTemplate(PensionPromptTemplate):
    """연금 개혁 특화 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.version = "2.0.0"
        self.metadata.tags.append("reform-focused")
    
    def get_system_prompt(self) -> str:
        """개혁 특화 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        reform_specific = """
        
연금 개혁 분석 특화 지침:
1. 개혁 필요성에 대한 인식 수준 평가
2. 구체적 개혁 방안에 대한 선호도 분석
3. 개혁 시나리오별 영향 평가
4. 이해관계자별 수용성 분석
5. 개혁 저항 요인 식별
6. 성공적 개혁을 위한 전제조건 도출

주요 개혁 옵션:
- 보험료율 인상
- 수급 연령 상향
- 소득대체율 조정
- 기초연금 강화
- 다층 연금 체계 구축
- 자동 조정 메커니즘 도입"""
        
        return base_prompt + reform_specific
    
    def get_output_schema(self) -> Dict[str, Any]:
        """개혁 특화 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "reform_analysis": {
                "necessity_recognition": "float (0.0 ~ 1.0)",
                "preferred_options": ["선호 개혁 방안"],
                "opposed_options": ["반대 개혁 방안"],
                "acceptance_level": "high/medium/low",
                "resistance_factors": ["저항 요인"],
                "success_conditions": ["성공 조건"],
                "timeline_preference": "immediate/gradual/delayed"
            },
            "scenario_impact": {
                "premium_increase": "영향 평가",
                "retirement_age_delay": "영향 평가",
                "benefit_reduction": "영향 평가",
                "multi_pillar_system": "영향 평가"
            }
        })
        
        return base_schema
