"""
Aspect-Based Sentiment Analysis (ABSA) 프롬프트 템플릿
"""
from typing import Dict, Any, List
from .base import BasePromptTemplate


class ABSAPromptTemplate(BasePromptTemplate):
    """ABSA 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["absa", "aspect", "sentiment", "detailed"]
        self.default_aspects = [
            "보험료",
            "급여",
            "연금개혁",
            "지속가능성",
            "세대간형평성",
            "정부정책",
            "투자수익률",
            "노후보장"
        ]
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 Aspect-Based Sentiment Analysis(ABSA) 전문가입니다.
        
        주요 작업:
        1. 텍스트에서 다양한 aspect(측면/주제)를 식별합니다
        2. 각 aspect에 대한 개별 감성을 분석합니다
        3. aspect 간의 관계와 중요도를 파악합니다
        4. 전체 맥락에서 각 aspect의 영향력을 평가합니다
        
        연금 도메인 핵심 aspect:
        - 보험료 (contribution rate)
        - 급여 수준 (benefit level)
        - 연금개혁 (pension reform)
        - 지속가능성 (sustainability)
        - 세대간 형평성 (intergenerational equity)
        - 정부 정책 (government policy)
        - 투자 수익률 (investment returns)
        - 노후 보장 (retirement security)
        
        각 aspect에 대해 정확하고 세밀한 감성 분석을 제공하며,
        반드시 지정된 JSON 형식으로 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        custom_aspects = kwargs.get('aspects', self.default_aspects)
        granularity = kwargs.get('granularity', 'detailed')  # detailed/simple
        
        prompt = f"""다음 텍스트에서 aspect별 감성을 분석해주세요.
        
분석 대상 텍스트:
{content}

주요 분석 aspect:
{', '.join(custom_aspects)}

분석 세부 수준: {granularity}

위 aspect 외에도 텍스트에서 중요한 aspect가 발견되면 추가로 분석해주세요.
각 aspect에 대해 구체적인 언급과 함께 감성을 평가해주세요."""
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "aspects": [
                {
                    "aspect": "aspect 이름",
                    "sentiment": "positive/negative/neutral/mixed",
                    "score": "float (-1.0 ~ 1.0)",
                    "confidence": "float (0.0 ~ 1.0)",
                    "mentions": ["관련 문장 또는 구절"],
                    "keywords": ["관련 키워드"],
                    "importance": "high/medium/low",
                    "evidence": "근거가 되는 텍스트"
                }
            ],
            "main_topics": ["주요 토픽1", "주요 토픽2"],
            "aspect_relations": [
                {
                    "aspect1": "aspect 이름",
                    "aspect2": "aspect 이름",
                    "relation": "관계 설명"
                }
            ],
            "overall_summary": "전체 ABSA 요약",
            "dominant_aspect": "가장 중요한 aspect",
            "sentiment_distribution": {
                "positive": "percentage",
                "negative": "percentage",
                "neutral": "percentage"
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """예시 반환"""
        return [
            {
                "input": "국민연금 보험료율을 인상하면 젊은 세대의 부담은 늘어나지만, 장기적으로 연금 재정의 지속가능성은 확보될 것입니다.",
                "output": {
                    "aspects": [
                        {
                            "aspect": "보험료",
                            "sentiment": "negative",
                            "score": -0.7,
                            "confidence": 0.9,
                            "mentions": ["보험료율을 인상하면", "부담은 늘어나지만"],
                            "keywords": ["인상", "부담"],
                            "importance": "high",
                            "evidence": "보험료율을 인상하면 젊은 세대의 부담은 늘어나지만"
                        },
                        {
                            "aspect": "지속가능성",
                            "sentiment": "positive",
                            "score": 0.8,
                            "confidence": 0.85,
                            "mentions": ["연금 재정의 지속가능성은 확보될 것"],
                            "keywords": ["지속가능성", "확보"],
                            "importance": "high",
                            "evidence": "장기적으로 연금 재정의 지속가능성은 확보될 것입니다"
                        },
                        {
                            "aspect": "세대간형평성",
                            "sentiment": "negative",
                            "score": -0.6,
                            "confidence": 0.8,
                            "mentions": ["젊은 세대의 부담은 늘어나"],
                            "keywords": ["젊은 세대", "부담"],
                            "importance": "medium",
                            "evidence": "젊은 세대의 부담은 늘어나지만"
                        }
                    ],
                    "main_topics": ["보험료 인상", "재정 지속가능성"],
                    "aspect_relations": [
                        {
                            "aspect1": "보험료",
                            "aspect2": "지속가능성",
                            "relation": "trade-off 관계"
                        }
                    ],
                    "overall_summary": "보험료 인상으로 인한 부담 증가와 지속가능성 확보 간의 균형",
                    "dominant_aspect": "보험료",
                    "sentiment_distribution": {
                        "positive": "33%",
                        "negative": "67%",
                        "neutral": "0%"
                    }
                }
            }
        ]


class PensionABSAPromptTemplate(ABSAPromptTemplate):
    """연금 특화 ABSA 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.version = "2.0.0"
        self.metadata.tags.append("pension-specific")
        
        # 연금 도메인 특화 aspects
        self.pension_aspects = {
            "financial": ["보험료", "급여수준", "수익률", "재정건전성"],
            "policy": ["연금개혁", "정부정책", "법제도", "정책변화"],
            "social": ["세대간형평성", "노후보장", "사회안전망", "복지"],
            "demographic": ["고령화", "출산율", "인구구조", "은퇴연령"],
            "economic": ["경제성장", "물가상승", "실업률", "소득수준"]
        }
    
    def get_system_prompt(self) -> str:
        """연금 특화 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        pension_specific = """
        
연금 도메인 특화 분석 지침:
1. 정책 변화의 영향을 다각도로 평가
2. 세대별 영향 차이를 명확히 구분
3. 단기적 영향 vs 장기적 영향 구분
4. 재정적 측면과 사회적 측면의 균형 고려
5. 국제 비교 관점 포함 (가능한 경우)
6. 정치적 중립성 유지

핵심 평가 기준:
- 공정성 (fairness)
- 적정성 (adequacy)  
- 지속가능성 (sustainability)
- 효율성 (efficiency)
- 형평성 (equity)"""
        
        return base_prompt + pension_specific
    
    def get_output_schema(self) -> Dict[str, Any]:
        """연금 특화 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "pension_specific_analysis": {
                "policy_impact": "정책 영향 평가",
                "generational_impact": {
                    "young": "청년층 영향",
                    "middle": "중년층 영향",
                    "elderly": "노년층 영향"
                },
                "timeline_impact": {
                    "short_term": "단기 영향",
                    "long_term": "장기 영향"
                },
                "sustainability_assessment": "지속가능성 평가",
                "reform_necessity": "개혁 필요성 (0-10)"
            }
        })
        
        return base_schema
