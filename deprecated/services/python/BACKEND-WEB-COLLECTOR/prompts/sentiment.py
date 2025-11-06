"""
감성 분석 프롬프트 템플릿
"""
from typing import Dict, Any, Optional
from .base import BasePromptTemplate


class SentimentPromptTemplate(BasePromptTemplate):
    """감성 분석용 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["sentiment", "emotion", "analysis"]
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 한국어 텍스트 감성 분석 전문가입니다.
        
        주어진 텍스트를 분석하여:
        1. 전체적인 감성 (긍정/부정/중립)을 판단합니다
        2. 감성 점수를 -1.0(매우 부정)에서 1.0(매우 긍정) 사이로 평가합니다
        3. 텍스트에서 드러나는 감정을 식별합니다
        4. 판단의 신뢰도를 0.0에서 1.0 사이로 평가합니다
        
        특히 연금, 금융, 정책 관련 내용에 민감하게 반응하며,
        객관적이고 정확한 분석을 제공합니다.
        
        반드시 지정된 JSON 형식으로만 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        context = kwargs.get('context', '')
        focus = kwargs.get('focus', '일반')
        
        prompt = f"다음 텍스트의 감성을 분석해주세요.\n\n"
        
        if context:
            prompt += f"맥락: {context}\n\n"
        
        if focus != '일반':
            prompt += f"분석 초점: {focus}\n\n"
        
        prompt += f"분석할 텍스트:\n{content}\n\n"
        prompt += "JSON 형식으로 응답해주세요."
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "overall_sentiment": "positive/negative/neutral",
            "sentiment_score": "float (-1.0 ~ 1.0)",
            "confidence": "float (0.0 ~ 1.0)",
            "emotions": ["감정1", "감정2"],
            "explanation": "분석 설명",
            "key_phrases": ["핵심 구문1", "핵심 구문2"],
            "context_considered": "고려된 맥락"
        }
    
    def get_examples(self) -> list:
        """예시 반환"""
        return [
            {
                "input": "국민연금 보험료 인상 소식에 많은 시민들이 우려를 표하고 있습니다.",
                "output": {
                    "overall_sentiment": "negative",
                    "sentiment_score": -0.6,
                    "confidence": 0.85,
                    "emotions": ["우려", "불안"],
                    "explanation": "보험료 인상에 대한 시민들의 부정적 반응이 명확히 드러남",
                    "key_phrases": ["보험료 인상", "우려를 표하고"],
                    "context_considered": "연금 정책 변경"
                }
            },
            {
                "input": "정부의 연금 개혁안이 장기적으로 지속가능성을 확보할 것으로 기대됩니다.",
                "output": {
                    "overall_sentiment": "positive",
                    "sentiment_score": 0.7,
                    "confidence": 0.9,
                    "emotions": ["기대", "희망"],
                    "explanation": "개혁안에 대한 긍정적 전망이 표현됨",
                    "key_phrases": ["지속가능성 확보", "기대됩니다"],
                    "context_considered": "연금 개혁"
                }
            }
        ]


class DetailedSentimentPromptTemplate(SentimentPromptTemplate):
    """상세 감성 분석 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags.extend(["detailed", "advanced"])
        self.metadata.version = "2.0.0"
    
    def get_system_prompt(self) -> str:
        """확장된 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        extended_prompt = """
        
        추가 분석 사항:
        1. 시간에 따른 감성 변화 패턴
        2. 문장별 감성 분포
        3. 주체별 감성 차이
        4. 암시적 감성 vs 명시적 감성
        5. 문화적 맥락 고려
        6. 아이러니나 풍자 감지
        """
        
        return base_prompt + extended_prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """확장된 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "sentence_sentiments": [
                {
                    "sentence": "문장",
                    "sentiment": "positive/negative/neutral",
                    "score": "float"
                }
            ],
            "subject_sentiments": {
                "정부": "sentiment",
                "시민": "sentiment",
                "전문가": "sentiment"
            },
            "implicit_sentiment": "감지된 암시적 감성",
            "irony_detected": "bool",
            "sentiment_trajectory": "increasing/decreasing/stable"
        })
        
        return base_schema
