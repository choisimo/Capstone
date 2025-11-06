"""
뉴스 분석 프롬프트 템플릿
"""
from typing import Dict, Any, List, Optional
from .base import BasePromptTemplate


class NewsAnalysisPromptTemplate(BasePromptTemplate):
    """뉴스 기사 분석 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["news", "media", "journalism", "analysis"]
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 뉴스 기사 분석 전문가입니다.
        
전문 역량:
1. 뉴스 기사의 핵심 내용 파악
2. 편향성 및 객관성 평가
3. 정보의 신뢰도 검증
4. 이해관계자 분석
5. 사회적 영향력 평가
6. 팩트체크 및 검증

분석 기준:
- 5W1H (Who, What, When, Where, Why, How)
- 정보원의 신뢰도
- 인용의 정확성
- 균형잡힌 보도 여부
- 숨겨진 의도나 편향
- 사실과 의견의 구분

저널리즘 원칙:
- 정확성 (Accuracy)
- 공정성 (Fairness)
- 균형성 (Balance)
- 투명성 (Transparency)
- 독립성 (Independence)

반드시 지정된 JSON 형식으로 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        url = kwargs.get('url', '')
        source = kwargs.get('source', '알 수 없음')
        date = kwargs.get('date', '')
        
        prompt = f"""다음 뉴스 기사를 종합적으로 분석해주세요.

출처: {source}
URL: {url}
날짜: {date}

기사 내용:
{content}

다음 사항들을 중점적으로 분석해주세요:
1. 기사의 주요 내용과 핵심 메시지
2. 헤드라인의 감성과 본문의 일치도
3. 이해관계자 및 영향받는 집단
4. 단기/장기 영향 평가
5. 예상되는 대중 반응
6. 정보의 신뢰도와 편향성
7. 관련 주제 및 후속 이슈"""
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "headline_sentiment": "positive/negative/neutral",
            "content_summary": "핵심 내용 요약",
            "key_facts": ["주요 사실1", "주요 사실2"],
            "stakeholders": {
                "primary": ["주요 이해관계자"],
                "secondary": ["부차적 이해관계자"]
            },
            "impact_assessment": {
                "short_term": "단기 영향",
                "long_term": "장기 영향",
                "affected_groups": ["영향받는 그룹"],
                "scale": "local/national/global"
            },
            "public_sentiment_prediction": "예상되는 대중 반응",
            "credibility_analysis": {
                "score": "float (0.0 ~ 1.0)",
                "sources_quality": "high/medium/low",
                "fact_check_needed": ["확인 필요 사항"],
                "evidence_strength": "strong/moderate/weak"
            },
            "bias_detection": {
                "detected": "bool",
                "type": "political/commercial/ideological/none",
                "direction": "편향 방향",
                "explanation": "설명"
            },
            "related_topics": ["관련 주제"],
            "follow_up_needed": "bool",
            "news_value": {
                "timeliness": "high/medium/low",
                "impact": "high/medium/low",
                "proximity": "high/medium/low",
                "prominence": "high/medium/low",
                "conflict": "high/medium/low"
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """예시 반환"""
        return [
            {
                "input": "정부가 국민연금 보험료율을 현행 9%에서 13%로 인상하는 개혁안을 발표했다. 이번 개혁안은 2025년부터 단계적으로 시행될 예정이며, 연금 고갈 시기를 2060년에서 2080년으로 연장하는 것을 목표로 한다.",
                "output": {
                    "headline_sentiment": "neutral",
                    "content_summary": "정부의 국민연금 보험료율 인상 개혁안 발표",
                    "key_facts": [
                        "보험료율 9%→13% 인상",
                        "2025년부터 단계적 시행",
                        "연금 고갈 시기 20년 연장 목표"
                    ],
                    "stakeholders": {
                        "primary": ["정부", "현 근로세대", "미래 수급자"],
                        "secondary": ["기업", "자영업자"]
                    },
                    "impact_assessment": {
                        "short_term": "근로자 실질소득 감소",
                        "long_term": "연금 재정 안정화",
                        "affected_groups": ["전체 가입자", "사업주"],
                        "scale": "national"
                    },
                    "public_sentiment_prediction": "부정적 반응 우세 예상",
                    "credibility_analysis": {
                        "score": 0.9,
                        "sources_quality": "high",
                        "fact_check_needed": ["구체적 시행 일정"],
                        "evidence_strength": "strong"
                    },
                    "bias_detection": {
                        "detected": False,
                        "type": "none",
                        "direction": "",
                        "explanation": "사실 위주의 객관적 보도"
                    },
                    "related_topics": ["연금개혁", "노후보장", "세대간형평성"],
                    "follow_up_needed": True,
                    "news_value": {
                        "timeliness": "high",
                        "impact": "high",
                        "proximity": "high",
                        "prominence": "high",
                        "conflict": "medium"
                    }
                }
            }
        ]


class PensionNewsPromptTemplate(NewsAnalysisPromptTemplate):
    """연금 관련 뉴스 특화 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.version = "2.0.0"
        self.metadata.tags.append("pension-news")
    
    def get_system_prompt(self) -> str:
        """연금 뉴스 특화 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        pension_news_specific = """
        
연금 뉴스 특화 분석:
1. 정책 변화의 구체적 내용과 시행 시기
2. 각 세대별 영향 분석
3. 재정 추계 및 전망의 신뢰도
4. 국제 비교 맥락
5. 정치적 배경과 의도
6. 전문가 의견의 균형성

핵심 체크포인트:
- 보험료율 변화
- 소득대체율 변화
- 수급 연령 조정
- 기금 운용 수익률
- 인구 전망 가정
- 경제 성장률 가정

주의사항:
- 숫자와 통계의 정확성 검증
- 장기 추계의 불확실성 명시
- 다양한 시나리오 고려
- 세대 간 갈등 조장 주의"""
        
        return base_prompt + pension_news_specific
    
    def get_output_schema(self) -> Dict[str, Any]:
        """연금 뉴스 특화 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "pension_specific": {
                "policy_changes": ["정책 변화 내용"],
                "implementation_timeline": "시행 일정",
                "financial_impact": {
                    "contribution_change": "보험료 변화",
                    "benefit_change": "급여 변화",
                    "sustainability_improvement": "지속가능성 개선도"
                },
                "generational_analysis": {
                    "winners": ["수혜 세대"],
                    "losers": ["부담 세대"],
                    "neutral": ["중립 세대"]
                },
                "expert_opinions": {
                    "supportive": ["지지 의견"],
                    "critical": ["비판 의견"],
                    "balanced": "균형 여부"
                }
            }
        })
        
        return base_schema
