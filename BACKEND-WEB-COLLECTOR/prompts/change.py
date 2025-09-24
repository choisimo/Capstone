"""
변경사항 분석 프롬프트 템플릿
"""
from typing import Dict, Any, List, Optional
from .base import BasePromptTemplate


class ChangeAnalysisPromptTemplate(BasePromptTemplate):
    """웹페이지 변경사항 분석 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["change", "diff", "monitoring", "analysis"]
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 웹 콘텐츠 변경사항 분석 전문가입니다.
        
전문 역량:
1. 변경사항의 중요도 평가
2. 의미적 차이 분석
3. 감성 변화 감지
4. 구조적 변경 식별
5. 패턴 기반 변화 예측
6. 알림 우선순위 결정

분석 기준:
- 변경 규모: 미세/소규모/중규모/대규모
- 변경 유형: 콘텐츠/구조/스타일/기능
- 중요도: 1-10 척도
- 긴급도: 높음/중간/낮음
- 영향 범위: 로컬/섹션/전체

변경 유형 분류:
- 콘텐츠 업데이트: 텍스트, 이미지, 비디오
- 구조 변경: 레이아웃, 네비게이션, 섹션
- 기능 변경: 링크, 폼, 인터랙션
- 메타데이터: 제목, 설명, 키워드
- 정책 변경: 약관, 가격, 규정

감성 변화 분석:
- 긍정 → 부정
- 부정 → 긍정
- 중립 → 감성적
- 강도 변화
- 톤 변화

알림 기준:
- 중대 변경: 즉시 알림
- 중요 변경: 우선 알림
- 일반 변경: 일괄 알림
- 미세 변경: 로그만 기록

반드시 지정된 JSON 형식으로 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        before = kwargs.get('before', '')
        after = kwargs.get('after', '')
        url = kwargs.get('url', '')
        monitoring_type = kwargs.get('monitoring_type', 'comprehensive')
        
        # content가 비어있으면 before/after 사용
        if not content and before and after:
            content = f"""
이전 내용:
{before[:2000]}

현재 내용:
{after[:2000]}
"""
        
        prompt = f"""다음 웹페이지 변경사항을 분석해주세요.

URL: {url}
모니터링 유형: {monitoring_type}

변경 내용:
{content}

다음 사항들을 중점적으로 분석해주세요:
1. 변경의 유형과 규모
2. 변경의 중요도 (1-10)
3. 감성이나 톤의 변화
4. 핵심 변경 사항 요약
5. 알림 필요 여부 및 긴급도
6. 영향받는 측면들
7. 후속 모니터링 필요사항"""
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "change_summary": {
                "type": "major/minor/cosmetic/structural",
                "scale": "micro/small/medium/large",
                "importance_score": "int (1-10)",
                "confidence": "float (0.0 ~ 1.0)"
            },
            "content_changes": {
                "added": ["추가된 내용"],
                "removed": ["제거된 내용"],
                "modified": ["수정된 내용"],
                "word_count_diff": "int",
                "key_changes": ["핵심 변경사항"]
            },
            "sentiment_analysis": {
                "before_sentiment": "positive/negative/neutral",
                "after_sentiment": "positive/negative/neutral",
                "sentiment_shift": "float (-1.0 ~ 1.0)",
                "tone_change": "설명",
                "emotion_changes": ["감정 변화"]
            },
            "structural_changes": {
                "layout_changed": "bool",
                "navigation_changed": "bool",
                "sections_added": ["추가된 섹션"],
                "sections_removed": ["제거된 섹션"],
                "ui_changes": ["UI 변경사항"]
            },
            "notification": {
                "required": "bool",
                "urgency": "immediate/high/medium/low",
                "channels": ["email/slack/sms/push"],
                "message": "알림 메시지",
                "recipients": ["수신자 그룹"]
            },
            "impact_assessment": {
                "affected_aspects": ["영향받는 측면"],
                "user_impact": "사용자 영향",
                "business_impact": "비즈니스 영향",
                "seo_impact": "SEO 영향"
            },
            "metadata": {
                "change_detected_at": "timestamp",
                "change_pattern": "패턴 설명",
                "related_changes": ["관련 변경사항"],
                "follow_up_actions": ["후속 조치"]
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """예시 반환"""
        return [
            {
                "input": """
이전 내용:
국민연금 보험료율은 현재 9%를 유지하고 있습니다.

현재 내용:
정부는 국민연금 보험료율을 9%에서 13%로 인상하는 개혁안을 발표했습니다. 이는 연금 재정 안정화를 위한 불가피한 선택이라고 설명했습니다.
""",
                "output": {
                    "change_summary": {
                        "type": "major",
                        "scale": "large",
                        "importance_score": 9,
                        "confidence": 0.95
                    },
                    "content_changes": {
                        "added": [
                            "13%로 인상하는 개혁안 발표",
                            "재정 안정화 위한 불가피한 선택"
                        ],
                        "removed": ["현재 9%를 유지"],
                        "modified": ["보험료율 정책"],
                        "word_count_diff": 25,
                        "key_changes": ["보험료율 4%p 인상 발표"]
                    },
                    "sentiment_analysis": {
                        "before_sentiment": "neutral",
                        "after_sentiment": "negative",
                        "sentiment_shift": -0.6,
                        "tone_change": "정보 전달 → 정책 정당화",
                        "emotion_changes": ["우려", "부담감"]
                    },
                    "structural_changes": {
                        "layout_changed": False,
                        "navigation_changed": False,
                        "sections_added": [],
                        "sections_removed": [],
                        "ui_changes": []
                    },
                    "notification": {
                        "required": True,
                        "urgency": "immediate",
                        "channels": ["email", "slack", "push"],
                        "message": "중대 정책 변경: 국민연금 보험료율 13% 인상 발표",
                        "recipients": ["all_users", "policy_watchers"]
                    },
                    "impact_assessment": {
                        "affected_aspects": ["보험료", "가계부담", "연금재정"],
                        "user_impact": "월 보험료 대폭 증가",
                        "business_impact": "기업 부담금 증가",
                        "seo_impact": "높은 검색 관심도 예상"
                    },
                    "metadata": {
                        "change_detected_at": "2025-09-24T10:00:00Z",
                        "change_pattern": "정책 발표 패턴",
                        "related_changes": ["연금개혁안 전체"],
                        "follow_up_actions": ["세부 내용 추적", "반응 모니터링"]
                    }
                }
            }
        ]


class IntelligentChangeAnalysisPromptTemplate(ChangeAnalysisPromptTemplate):
    """지능형 변경 분석 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.version = "2.0.0"
        self.metadata.tags.append("intelligent")
    
    def get_system_prompt(self) -> str:
        """지능형 분석 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        intelligent_specific = """
        
지능형 분석 기능:
1. 변경 패턴 학습 및 예측
2. 이상 변경 감지
3. 변경 의도 추론
4. 연쇄 변경 예측
5. 자동 중요도 조정

패턴 인식:
- 정기적 업데이트 패턴
- 이벤트 기반 변경
- 점진적 변화 추세
- 급격한 변화 신호
- 은폐된 변경 감지

예측 분석:
- 다음 변경 시점 예측
- 변경 규모 예상
- 연관 페이지 변경 예측
- 사용자 반응 예측

컨텍스트 분석:
- 시장 상황 고려
- 경쟁사 동향 반영
- 규제 변화 연관성
- 계절적 요인
- 이벤트 상관관계

학습 메커니즘:
- 과거 패턴 학습
- 정확도 피드백 반영
- 도메인 지식 축적
- 예외 상황 학습"""
        
        return base_prompt + intelligent_specific
    
    def get_output_schema(self) -> Dict[str, Any]:
        """지능형 분석 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "intelligent_analysis": {
                "change_pattern": {
                    "type": "정기적/이벤트/점진적/급격한",
                    "frequency": "빈도",
                    "predictability": "float (0.0 ~ 1.0)",
                    "anomaly_score": "float (0.0 ~ 1.0)"
                },
                "intent_analysis": {
                    "likely_intent": "추정 의도",
                    "confidence": "float",
                    "evidence": ["근거"],
                    "hidden_changes": ["은폐된 변경"]
                },
                "predictions": {
                    "next_change_eta": "예상 시점",
                    "next_change_type": "예상 유형",
                    "cascade_changes": ["연쇄 변경 예측"],
                    "trend_direction": "상승/하락/유지"
                },
                "contextual_factors": {
                    "market_correlation": "시장 연관성",
                    "competitor_influence": "경쟁사 영향",
                    "regulatory_impact": "규제 영향",
                    "seasonal_factor": "계절 요인"
                }
            },
            "learning_feedback": {
                "pattern_matched": "bool",
                "accuracy_score": "float",
                "new_pattern_detected": "bool",
                "knowledge_update": "업데이트 내용"
            }
        })
        
        return base_schema
