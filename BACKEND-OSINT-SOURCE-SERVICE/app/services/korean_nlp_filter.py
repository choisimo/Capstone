"""
한국어 NLP 기반 관련성 필터링 시스템
PRD 기반 구현 - 85% 이상 정확도 목표
"""

import re
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# NLP 라이브러리
try:
    from konlpy.tag import Okt, Kkma, Komoran
except ImportError:
    print("KoNLPy 설치 필요: pip install konlpy")
    Okt = Kkma = Komoran = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """관련성 점수"""
    overall_score: float
    keyword_score: float
    entity_score: float
    semantic_score: float
    is_relevant: bool
    confidence: float
    reason: str


class KoreanTextNormalizer:
    """한국어 텍스트 정규화"""
    
    def __init__(self):
        # 불필요한 패턴
        self.noise_patterns = [
            r'\[.*?\]',  # 대괄호 내용
            r'\(.*?\)',  # 소괄호 내용
            r'<.*?>',    # HTML 태그
            r'http[s]?://[^\s]+',  # URL
            r'[^\w\s가-힣]',  # 특수문자 (한글, 영문, 숫자 제외)
        ]
        
        # 한국어 조사
        self.particles = [
            '은', '는', '이', '가', '을', '를', '에', '에서', 
            '으로', '로', '와', '과', '의', '도', '만', '부터', 
            '까지', '에게', '한테', '께'
        ]
    
    def normalize(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""
        
        # 소문자 변환
        text = text.lower()
        
        # 노이즈 제거
        for pattern in self.noise_patterns:
            text = re.sub(pattern, ' ', text)
        
        # 중복 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def remove_particles(self, text: str) -> str:
        """조사 제거"""
        words = text.split()
        processed_words = []
        
        for word in words:
            # 조사로 끝나는 경우 제거
            for particle in self.particles:
                if word.endswith(particle):
                    word = word[:-len(particle)]
                    break
            processed_words.append(word)
        
        return ' '.join(processed_words)


class KoreanEntityExtractor:
    """한국어 개체명 추출"""
    
    def __init__(self):
        self.morpheme_analyzer = Okt() if Okt else None
        
        # 국민연금 관련 핵심 개체
        self.pension_entities = [
            '국민연금', '국연', '연금', '노후', '은퇴', '퇴직',
            '보험료', '납부', '수급', '급여', '연금액', '소득대체율',
            '국민연금공단', '보건복지부', '복지부', 'NPS'
        ]
        
        # 금융 관련 개체
        self.finance_entities = [
            '투자', '수익률', '운용', '자산', '기금', '주식',
            '채권', '부동산', '포트폴리오', '리스크'
        ]
        
        # 정책 관련 개체
        self.policy_entities = [
            '개혁', '정책', '법안', '제도', '개선', '인상',
            '감소', '확대', '축소', '변경'
        ]
    
    def extract_entities(self, text: str) -> List[Dict]:
        """개체명 추출"""
        entities = []
        
        # 정규화
        normalizer = KoreanTextNormalizer()
        normalized_text = normalizer.normalize(text)
        
        # 국민연금 관련 개체 검색
        for entity in self.pension_entities:
            if entity in normalized_text:
                entities.append({
                    'text': entity,
                    'type': 'PENSION',
                    'category': '연금'
                })
        
        # 금융 관련 개체 검색
        for entity in self.finance_entities:
            if entity in normalized_text:
                entities.append({
                    'text': entity,
                    'type': 'FINANCE',
                    'category': '금융'
                })
        
        # 정책 관련 개체 검색
        for entity in self.policy_entities:
            if entity in normalized_text:
                entities.append({
                    'text': entity,
                    'type': 'POLICY',
                    'category': '정책'
                })
        
        # 형태소 분석을 통한 추가 개체 추출
        if self.morpheme_analyzer:
            try:
                nouns = self.morpheme_analyzer.nouns(normalized_text)
                for noun in nouns:
                    if len(noun) >= 2:  # 2글자 이상 명사
                        # 중복 확인
                        if not any(e['text'] == noun for e in entities):
                            entities.append({
                                'text': noun,
                                'type': 'NOUN',
                                'category': '일반명사'
                            })
            except:
                pass
        
        return entities


class SemanticSimilarityCalculator:
    """의미 유사도 계산"""
    
    def __init__(self):
        self.normalizer = KoreanTextNormalizer()
        
        # 국민연금 관련 시맨틱 그룹
        self.semantic_groups = {
            '연금수급': ['수급', '급여', '지급', '수령', '연금액'],
            '보험료': ['납부', '보험료', '기여금', '부담금'],
            '투자운용': ['투자', '운용', '수익률', '포트폴리오', '자산배분'],
            '정책개혁': ['개혁', '개선', '정책', '제도', '변경'],
            '노후준비': ['노후', '은퇴', '퇴직', '준비', '대비']
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 의미 유사도 계산"""
        
        # 정규화
        norm_text1 = self.normalizer.normalize(text1)
        norm_text2 = self.normalizer.normalize(text2)
        
        # 단어 집합 생성
        words1 = set(norm_text1.split())
        words2 = set(norm_text2.split())
        
        # Jaccard 유사도
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        jaccard_score = len(intersection) / len(union) if union else 0
        
        # 시맨틱 그룹 기반 유사도
        semantic_score = self._calculate_semantic_group_similarity(words1, words2)
        
        # 가중 평균
        final_score = (jaccard_score * 0.6) + (semantic_score * 0.4)
        
        return min(1.0, final_score)
    
    def _calculate_semantic_group_similarity(self, words1: set, words2: set) -> float:
        """시맨틱 그룹 기반 유사도"""
        score = 0.0
        count = 0
        
        for group_name, group_words in self.semantic_groups.items():
            group_set = set(group_words)
            
            # 두 텍스트가 같은 시맨틱 그룹에 속하는지 확인
            matches1 = words1 & group_set
            matches2 = words2 & group_set
            
            if matches1 and matches2:
                score += 1.0
                count += 1
            elif matches1 or matches2:
                score += 0.5
                count += 1
        
        return score / count if count > 0 else 0.0


class KoreanRelevanceFilter:
    """
    한국어 관련성 필터링 엔진
    PRD 명세: 85% 이상 정확도 목표
    """
    
    def __init__(self):
        self.normalizer = KoreanTextNormalizer()
        self.entity_extractor = KoreanEntityExtractor()
        self.similarity_calculator = SemanticSimilarityCalculator()
        
        # 관련성 임계값
        self.relevance_threshold = 0.75  # PRD: 75% 이상
        
        # 필터링 통계
        self.stats = {
            'total_processed': 0,
            'relevant_count': 0,
            'filtered_count': 0,
            'avg_relevance_score': 0.0
        }
    
    def calculate_relevance(
        self, 
        content: str, 
        search_term: str,
        reference_content: Optional[str] = None
    ) -> RelevanceScore:
        """
        관련성 점수 계산
        
        Args:
            content: 평가할 콘텐츠
            search_term: 검색어
            reference_content: 참조 콘텐츠 (뉴스 등)
        
        Returns:
            RelevanceScore 객체
        """
        
        if not content or not search_term:
            return RelevanceScore(
                overall_score=0.0,
                keyword_score=0.0,
                entity_score=0.0,
                semantic_score=0.0,
                is_relevant=False,
                confidence=0.0,
                reason="콘텐츠 또는 검색어 없음"
            )
        
        # 1. 키워드 매칭 점수
        keyword_score = self._calculate_keyword_score(content, search_term)
        
        # 2. 개체명 매칭 점수
        entity_score = self._calculate_entity_score(content, search_term)
        
        # 3. 의미 유사도 점수
        semantic_score = self.similarity_calculator.calculate_similarity(content, search_term)
        
        # 4. 참조 콘텐츠와의 유사도 (있는 경우)
        reference_score = 0.0
        if reference_content:
            reference_score = self.similarity_calculator.calculate_similarity(content, reference_content)
        
        # 종합 점수 계산 (가중 평균)
        if reference_content:
            overall_score = (
                keyword_score * 0.25 +
                entity_score * 0.25 +
                semantic_score * 0.25 +
                reference_score * 0.25
            )
        else:
            overall_score = (
                keyword_score * 0.35 +
                entity_score * 0.35 +
                semantic_score * 0.30
            )
        
        # 관련성 판단
        is_relevant = overall_score >= self.relevance_threshold
        
        # 신뢰도 계산
        confidence = min(1.0, overall_score * 1.2) if is_relevant else overall_score
        
        # 판단 이유
        if is_relevant:
            reason = f"관련성 높음 (점수: {overall_score:.2f})"
        else:
            reason = f"관련성 낮음 (점수: {overall_score:.2f})"
        
        # 통계 업데이트
        self._update_statistics(overall_score, is_relevant)
        
        return RelevanceScore(
            overall_score=overall_score,
            keyword_score=keyword_score,
            entity_score=entity_score,
            semantic_score=semantic_score,
            is_relevant=is_relevant,
            confidence=confidence,
            reason=reason
        )
    
    def _calculate_keyword_score(self, content: str, search_term: str) -> float:
        """키워드 매칭 점수"""
        # 정규화
        norm_content = self.normalizer.normalize(content)
        norm_search = self.normalizer.normalize(search_term)
        
        # 검색어 분할
        search_words = norm_search.split()
        
        # 각 검색어의 출현 빈도 계산
        total_score = 0.0
        for word in search_words:
            count = norm_content.count(word)
            # 로그 스케일 적용 (너무 많이 나와도 1.0 넘지 않도록)
            word_score = min(1.0, count / 10.0)
            total_score += word_score
        
        # 평균 점수
        avg_score = total_score / len(search_words) if search_words else 0.0
        
        return min(1.0, avg_score)
    
    def _calculate_entity_score(self, content: str, search_term: str) -> float:
        """개체명 매칭 점수"""
        # 콘텐츠에서 개체 추출
        content_entities = self.entity_extractor.extract_entities(content)
        search_entities = self.entity_extractor.extract_entities(search_term)
        
        if not search_entities:
            return 0.5  # 검색어에 특별한 개체가 없으면 중립 점수
        
        # 매칭되는 개체 수 계산
        content_entity_texts = {e['text'] for e in content_entities}
        search_entity_texts = {e['text'] for e in search_entities}
        
        matches = content_entity_texts & search_entity_texts
        
        if not search_entity_texts:
            return 0.0
        
        # 매칭 비율
        match_ratio = len(matches) / len(search_entity_texts)
        
        # 중요 개체(PENSION) 가중치 부여
        important_matches = sum(
            1 for e in content_entities 
            if e['text'] in matches and e['type'] == 'PENSION'
        )
        
        if important_matches > 0:
            match_ratio = min(1.0, match_ratio * 1.5)
        
        return match_ratio
    
    def _update_statistics(self, score: float, is_relevant: bool):
        """통계 업데이트"""
        self.stats['total_processed'] += 1
        
        if is_relevant:
            self.stats['relevant_count'] += 1
        else:
            self.stats['filtered_count'] += 1
        
        # 평균 점수 업데이트
        n = self.stats['total_processed']
        prev_avg = self.stats['avg_relevance_score']
        self.stats['avg_relevance_score'] = (prev_avg * (n - 1) + score) / n
    
    def filter_articles(self, articles: List[Dict], search_term: str) -> List[Dict]:
        """
        기사 목록 필터링
        
        Args:
            articles: 기사 목록
            search_term: 검색어
        
        Returns:
            필터링된 기사 목록
        """
        filtered_articles = []
        
        for article in articles:
            # URL 유효성 필터링 (존재하는 경우 http/https만 허용)
            url = article.get('url', '')
            if url and not url.startswith(('http://', 'https://')):
                logger.debug(f"무효 URL로 필터링: {url}")
                continue
            # 제목과 내용 결합
            content = f"{article.get('title', '')} {article.get('content', '')}"
            
            # 관련성 계산
            relevance = self.calculate_relevance(content, search_term)
            
            if relevance.is_relevant:
                # 관련성 점수 추가
                article['relevance_score'] = relevance.overall_score
                article['relevance_confidence'] = relevance.confidence
                filtered_articles.append(article)
            else:
                logger.debug(f"필터링됨: {article.get('title', 'Unknown')} - {relevance.reason}")
        
        # 관련성 점수로 정렬
        filtered_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return filtered_articles
    
    def get_statistics(self) -> Dict:
        """통계 반환"""
        return {
            **self.stats,
            'relevance_rate': (
                self.stats['relevant_count'] / max(self.stats['total_processed'], 1) * 100
            ),
            'filter_rate': (
                self.stats['filtered_count'] / max(self.stats['total_processed'], 1) * 100
            )
        }


# 테스트
def test_korean_relevance_filter():
    """한국어 관련성 필터 테스트"""
    filter = KoreanRelevanceFilter()
    
    # 테스트 케이스
    test_cases = [
        {
            'content': '국민연금 보험료가 인상될 예정입니다. 노후 준비를 위한 연금 개혁이 필요합니다.',
            'search_term': '국민연금',
            'expected': True
        },
        {
            'content': '오늘 날씨가 매우 좋습니다. 영화를 보러 갈 예정입니다.',
            'search_term': '국민연금',
            'expected': False
        },
        {
            'content': '연금 수급 연령이 65세로 상향 조정되었습니다. 은퇴 준비가 중요합니다.',
            'search_term': '국민연금 수급',
            'expected': True
        },
        {
            'content': 'NATO 정상회의가 열렸습니다. 국제 안보 문제를 논의했습니다.',
            'search_term': '국민연금',
            'expected': False
        }
    ]
    
    print("=" * 60)
    print("한국어 관련성 필터 테스트")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        result = filter.calculate_relevance(test['content'], test['search_term'])
        
        # 결과 검증
        success = result.is_relevant == test['expected']
        status = "✅" if success else "❌"
        
        print(f"\n테스트 {i}: {status}")
        print(f"  콘텐츠: {test['content'][:50]}...")
        print(f"  검색어: {test['search_term']}")
        print(f"  예상: {test['expected']}, 실제: {result.is_relevant}")
        print(f"  점수: {result.overall_score:.2f}")
        print(f"    - 키워드: {result.keyword_score:.2f}")
        print(f"    - 개체명: {result.entity_score:.2f}")
        print(f"    - 의미: {result.semantic_score:.2f}")
        print(f"  이유: {result.reason}")
    
    # 통계 출력
    stats = filter.get_statistics()
    print(f"\n📊 통계:")
    print(f"  처리: {stats['total_processed']}건")
    print(f"  관련: {stats['relevant_count']}건 ({stats['relevance_rate']:.1f}%)")
    print(f"  필터: {stats['filtered_count']}건 ({stats['filter_rate']:.1f}%)")
    print(f"  평균 점수: {stats['avg_relevance_score']:.2f}")


if __name__ == "__main__":
    test_korean_relevance_filter()
