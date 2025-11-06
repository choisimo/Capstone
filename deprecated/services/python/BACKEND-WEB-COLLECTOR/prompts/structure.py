"""
웹 구조 학습 프롬프트 템플릿
"""
from typing import Dict, Any, List, Optional
from .base import BasePromptTemplate


class StructureLearningPromptTemplate(BasePromptTemplate):
    """웹페이지 구조 학습 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.tags = ["structure", "extraction", "web", "scraping"]
        
        self.target_fields = [
            "title",
            "content",
            "author",
            "date",
            "category",
            "tags",
            "summary",
            "image",
            "source"
        ]
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 웹 스크래핑 및 데이터 추출 전문가입니다.
        
주요 역량:
1. HTML/CSS 구조 분석
2. 데이터 추출 패턴 식별
3. CSS 셀렉터 및 XPath 생성
4. 동적 콘텐츠 감지
5. 구조 변화 예측
6. 추출 신뢰도 평가

분석 기법:
- DOM 트리 구조 파악
- 시맨틱 HTML 태그 활용
- 클래스명/ID 패턴 분석
- 데이터 속성 활용
- 마이크로데이터/스키마 인식
- 반복 패턴 식별

웹사이트 유형별 특징:
- 뉴스: article, time, author 태그
- 블로그: post, entry, content 클래스
- 포럼: thread, reply, user 구조
- 소셜미디어: feed, status, timeline
- 정부: table, report, document

추출 전략:
1. 가장 구체적인 셀렉터 우선
2. 여러 대안 셀렉터 제공
3. 동적 콘텐츠 플래그 표시
4. 페이지네이션 패턴 인식
5. 중복 제거 전략

반드시 지정된 JSON 형식으로 응답합니다."""
    
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        url = kwargs.get('url', '')
        page_type = kwargs.get('page_type', 'auto-detect')
        target_fields = kwargs.get('target_fields', self.target_fields)
        sample_count = kwargs.get('sample_count', 1)
        
        prompt = f"""다음 HTML 구조를 분석하여 데이터 추출 템플릿을 생성해주세요.

URL: {url}
페이지 유형: {page_type}
샘플 수: {sample_count}

HTML 구조:
{content[:5000]}  # 처음 5000자만 제공

추출 대상 필드:
{', '.join(target_fields)}

각 필드에 대해:
1. 가장 정확한 CSS 셀렉터 제공
2. 대체 XPath 제공 (CSS 셀렉터가 불안정한 경우)
3. 추출 신뢰도 평가
4. 잠재적 문제점 식별
5. 데이터 정제 필요사항"""
        
        return prompt
    
    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "structure": {
                "title": {
                    "css_selector": "CSS 셀렉터",
                    "xpath": "XPath (옵션)",
                    "attribute": "text/href/src 등",
                    "confidence": "float (0.0 ~ 1.0)",
                    "fallback_selectors": ["대체 셀렉터"],
                    "preprocessing": "필요한 전처리"
                },
                "content": {
                    "css_selector": "CSS 셀렉터",
                    "xpath": "XPath",
                    "attribute": "text",
                    "confidence": "float",
                    "multiple": "bool (여러 요소)",
                    "join_method": "결합 방법"
                },
                "date": {
                    "css_selector": "CSS 셀렉터",
                    "xpath": "XPath",
                    "attribute": "datetime/text",
                    "format": "날짜 형식",
                    "confidence": "float"
                },
                "author": {
                    "css_selector": "CSS 셀렉터",
                    "xpath": "XPath",
                    "attribute": "text",
                    "confidence": "float"
                }
            },
            "page_analysis": {
                "type": "news/blog/forum/social/government/other",
                "language": "ko/en/mixed",
                "encoding": "UTF-8",
                "dynamic_content": "bool",
                "javascript_required": "bool",
                "ajax_loading": "bool"
            },
            "extraction_metadata": {
                "overall_confidence": "float (0.0 ~ 1.0)",
                "recommended_method": "css/xpath/mixed",
                "update_frequency": "실시간/일일/주간",
                "pagination": {
                    "detected": "bool",
                    "type": "numbered/infinite-scroll/load-more",
                    "selector": "페이지네이션 셀렉터"
                }
            },
            "potential_issues": ["잠재적 문제점"],
            "extraction_hints": ["추출 힌트"],
            "validation_rules": {
                "title": "검증 규칙",
                "content": "최소 길이 등",
                "date": "날짜 형식 검증"
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """예시 반환"""
        return [
            {
                "input": '<article class="news-article"><h1 class="article-title">연금 개혁안 발표</h1><div class="article-meta"><span class="author">김기자</span><time datetime="2025-09-24">2025년 9월 24일</time></div><div class="article-body">본문 내용...</div></article>',
                "output": {
                    "structure": {
                        "title": {
                            "css_selector": "article.news-article h1.article-title",
                            "xpath": "//article[@class='news-article']/h1[@class='article-title']",
                            "attribute": "text",
                            "confidence": 0.95,
                            "fallback_selectors": ["h1", ".article-title"],
                            "preprocessing": "trim"
                        },
                        "content": {
                            "css_selector": "div.article-body",
                            "xpath": "//div[@class='article-body']",
                            "attribute": "text",
                            "confidence": 0.9,
                            "multiple": False,
                            "join_method": "paragraph"
                        },
                        "date": {
                            "css_selector": "time[datetime]",
                            "xpath": "//time[@datetime]",
                            "attribute": "datetime",
                            "format": "YYYY-MM-DD",
                            "confidence": 0.95
                        },
                        "author": {
                            "css_selector": "span.author",
                            "xpath": "//span[@class='author']",
                            "attribute": "text",
                            "confidence": 0.85
                        }
                    },
                    "page_analysis": {
                        "type": "news",
                        "language": "ko",
                        "encoding": "UTF-8",
                        "dynamic_content": False,
                        "javascript_required": False,
                        "ajax_loading": False
                    },
                    "extraction_metadata": {
                        "overall_confidence": 0.91,
                        "recommended_method": "css",
                        "update_frequency": "일일",
                        "pagination": {
                            "detected": False,
                            "type": "none",
                            "selector": ""
                        }
                    },
                    "potential_issues": [
                        "클래스명이 변경될 수 있음",
                        "동적 로딩 콘텐츠 확인 필요"
                    ],
                    "extraction_hints": [
                        "article 태그로 기사 구분",
                        "time 태그의 datetime 속성 활용"
                    ],
                    "validation_rules": {
                        "title": "길이 > 5",
                        "content": "길이 > 100",
                        "date": "ISO 형식"
                    }
                }
            }
        ]


class AdaptiveStructureLearningPromptTemplate(StructureLearningPromptTemplate):
    """적응형 구조 학습 프롬프트 템플릿"""
    
    def __init__(self):
        super().__init__()
        self.metadata.version = "2.0.0"
        self.metadata.tags.append("adaptive")
    
    def get_system_prompt(self) -> str:
        """적응형 학습 시스템 프롬프트"""
        base_prompt = super().get_system_prompt()
        
        adaptive_specific = """
        
적응형 학습 전략:
1. 구조 변화 패턴 학습
2. 시간에 따른 변화 추적
3. 유사 사이트 패턴 활용
4. 자동 복구 전략
5. 신뢰도 기반 전환

변화 감지 및 대응:
- 셀렉터 실패 시 자동 대안 탐색
- 부분 매칭으로 근사 추출
- 컨텍스트 기반 추론
- 이전 성공 패턴 재활용

학습 메커니즘:
- 성공/실패 피드백 반영
- 신뢰도 점수 업데이트
- 패턴 일반화
- 도메인 특화 규칙 생성"""
        
        return base_prompt + adaptive_specific
    
    def get_output_schema(self) -> Dict[str, Any]:
        """적응형 학습 출력 스키마"""
        base_schema = super().get_output_schema()
        
        base_schema.update({
            "adaptive_strategy": {
                "primary_method": "메인 추출 전략",
                "fallback_chain": ["대체 전략 순서"],
                "confidence_threshold": "float",
                "learning_rate": "float",
                "adaptation_triggers": ["적응 트리거 조건"]
            },
            "pattern_library": {
                "domain_patterns": ["도메인 특화 패턴"],
                "generic_patterns": ["일반 패턴"],
                "learned_patterns": ["학습된 패턴"]
            },
            "change_resilience": {
                "expected_changes": ["예상 변화"],
                "recovery_strategies": ["복구 전략"],
                "monitoring_points": ["모니터링 포인트"]
            }
        })
        
        return base_schema
