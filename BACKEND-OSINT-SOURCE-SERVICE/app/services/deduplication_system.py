"""
데이터 중복 제거 시스템
PRD 기반 구현 - SimHash와 Bloom Filter 활용
"""

import hashlib
import json
import re
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLNormalizer:
    """URL 정규화"""
    
    @staticmethod
    def normalize(url: str) -> str:
        """
        URL 정규화
        - 소문자 변환
        - 쿼리 파라미터 정렬
        - Fragment 제거
        - 중복 슬래시 제거
        """
        if not url:
            return ""
        
        try:
            # URL 파싱
            parsed = urlparse(url.lower())
            
            # 쿼리 파라미터 정렬
            query_params = parse_qs(parsed.query)
            sorted_query = urlencode(sorted(query_params.items()), doseq=True)
            
            # Path 정규화 (끝 슬래시 제거, 중복 슬래시 제거)
            path = re.sub(r'/+', '/', parsed.path)
            path = path.rstrip('/')
            
            # 재조합
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                sorted_query,
                ''  # Fragment 제거
            ))
            
            return normalized
            
        except Exception as e:
            logger.error(f"URL 정규화 실패: {url} - {e}")
            return url


class SimHash:
    """SimHash 구현"""
    
    def __init__(self, value: str, hashbits: int = 64):
        self.hashbits = hashbits
        self.value = value
        self.hash = self._calculate_hash(value)
    
    def _calculate_hash(self, content: str) -> int:
        """SimHash 계산"""
        # 토큰화
        tokens = self._tokenize(content)
        
        # 각 토큰의 해시 계산
        v = [0] * self.hashbits
        
        for token in tokens:
            # 토큰 해시
            token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
            
            # 비트별 가중치 적용
            for i in range(self.hashbits):
                bitmask = 1 << i
                if token_hash & bitmask:
                    v[i] += 1
                else:
                    v[i] -= 1
        
        # 최종 해시 생성
        fingerprint = 0
        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint |= 1 << i
        
        return fingerprint
    
    def _tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화"""
        # 한국어 처리를 위한 간단한 토큰화
        text = text.lower()
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        # 공백으로 분리
        tokens = text.split()
        # 2-gram 생성
        ngrams = []
        for i in range(len(tokens) - 1):
            ngrams.append(tokens[i] + tokens[i + 1])
        return tokens + ngrams
    
    def hamming_distance(self, other: 'SimHash') -> int:
        """해밍 거리 계산"""
        x = self.hash ^ other.hash
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance


class BloomFilter:
    """Bloom Filter 구현"""
    
    def __init__(self, capacity: int = 1000000, error_rate: float = 0.001):
        """
        Args:
            capacity: 예상 항목 수
            error_rate: False positive 확률
        """
        # 최적 크기 계산
        self.size = self._optimal_size(capacity, error_rate)
        self.hash_count = self._optimal_hash_count(self.size, capacity)
        
        # 비트 배열
        self.bit_array = [False] * self.size
        self.count = 0
        
        logger.info(f"Bloom Filter 생성: size={self.size}, hash_count={self.hash_count}")
    
    def _optimal_size(self, n: int, p: float) -> int:
        """최적 비트 배열 크기 계산"""
        import math
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)
    
    def _optimal_hash_count(self, m: int, n: int) -> int:
        """최적 해시 함수 개수 계산"""
        import math
        k = (m / n) * math.log(2)
        return int(k)
    
    def _hash(self, item: str, seed: int) -> int:
        """해시 계산"""
        hash_value = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(hash_value, 16) % self.size
    
    def add(self, item: str):
        """항목 추가"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = True
        self.count += 1
    
    def contains(self, item: str) -> bool:
        """항목 존재 여부 확인"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True
    
    def __contains__(self, item: str) -> bool:
        return self.contains(item)


class DeduplicationEngine:
    """
    중복 제거 엔진
    PRD 명세: < 2% 중복률 목표
    """
    
    def __init__(self, similarity_threshold: int = 3):
        """
        Args:
            similarity_threshold: SimHash 해밍 거리 임계값 (낮을수록 엄격)
        """
        # URL 중복 확인용 Bloom Filter
        self.url_bloom = BloomFilter(capacity=1000000, error_rate=0.001)
        self.url_cache = set()  # 정확한 확인용
        
        # 콘텐츠 중복 확인용 SimHash
        self.simhash_index = {}  # hash -> content_id
        self.similarity_threshold = similarity_threshold
        
        # URL 정규화
        self.url_normalizer = URLNormalizer()
        
        # 통계
        self.stats = {
            'total_checked': 0,
            'duplicates_found': 0,
            'near_duplicates_found': 0,
            'unique_items': 0
        }
    
    def is_duplicate_url(self, url: str) -> bool:
        """URL 중복 확인"""
        # 정규화
        normalized_url = self.url_normalizer.normalize(url)
        
        # Bloom Filter로 빠른 확인
        if normalized_url in self.url_bloom:
            # 정확한 확인
            if normalized_url in self.url_cache:
                self.stats['duplicates_found'] += 1
                logger.debug(f"중복 URL 감지: {normalized_url}")
                return True
        
        # 새로운 URL 등록
        self.url_bloom.add(normalized_url)
        self.url_cache.add(normalized_url)
        
        return False
    
    def is_duplicate_content(self, content: str, content_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        콘텐츠 중복 확인 (Near-duplicate 포함)
        
        Returns:
            (is_duplicate, similar_content_id)
        """
        if not content:
            return False, None
        
        # SimHash 생성
        simhash = SimHash(content)
        
        # Near-duplicate 검사
        for existing_hash, existing_id in self.simhash_index.items():
            existing_simhash = SimHash(content)
            existing_simhash.hash = existing_hash
            
            distance = simhash.hamming_distance(existing_simhash)
            
            if distance <= self.similarity_threshold:
                self.stats['near_duplicates_found'] += 1
                logger.debug(f"Near-duplicate 감지: 해밍 거리={distance}, ID={existing_id}")
                return True, existing_id
        
        # 새로운 콘텐츠 등록
        if content_id:
            self.simhash_index[simhash.hash] = content_id
        else:
            content_id = hashlib.md5(content.encode()).hexdigest()[:16]
            self.simhash_index[simhash.hash] = content_id
        
        self.stats['unique_items'] += 1
        return False, None
    
    def check_duplicate(self, item: Dict) -> Dict:
        """
        통합 중복 확인
        
        Args:
            item: {
                'url': str,
                'content': str,
                'title': str,
                'id': str (optional)
            }
        
        Returns:
            {
                'is_duplicate': bool,
                'duplicate_type': 'url' | 'content' | 'near_duplicate' | None,
                'similar_id': str (if near-duplicate),
                'confidence': float
            }
        """
        self.stats['total_checked'] += 1
        
        # URL 중복 확인
        if 'url' in item:
            if self.is_duplicate_url(item['url']):
                return {
                    'is_duplicate': True,
                    'duplicate_type': 'url',
                    'similar_id': None,
                    'confidence': 1.0
                }
        
        # 콘텐츠 중복 확인
        if 'content' in item:
            is_dup, similar_id = self.is_duplicate_content(
                item['content'], 
                item.get('id')
            )
            
            if is_dup:
                return {
                    'is_duplicate': True,
                    'duplicate_type': 'near_duplicate' if similar_id else 'content',
                    'similar_id': similar_id,
                    'confidence': 0.95  # Near-duplicate는 신뢰도 약간 낮춤
                }
        
        # 제목 기반 추가 확인 (선택적)
        if 'title' in item:
            title_hash = hashlib.md5(item['title'].encode()).hexdigest()
            # 제목은 Bloom Filter만 사용 (빠른 확인)
            if title_hash in self.url_bloom:  # URL bloom을 재사용
                logger.warning(f"제목 중복 가능성: {item['title']}")
        
        return {
            'is_duplicate': False,
            'duplicate_type': None,
            'similar_id': None,
            'confidence': 0.0
        }
    
    def deduplicate_list(self, items: List[Dict]) -> List[Dict]:
        """
        리스트 중복 제거
        
        Args:
            items: 중복 제거할 항목 리스트
        
        Returns:
            중복이 제거된 리스트
        """
        unique_items = []
        
        for item in items:
            result = self.check_duplicate(item)
            
            if not result['is_duplicate']:
                unique_items.append(item)
            else:
                logger.debug(
                    f"중복 제거: {item.get('title', 'Unknown')} "
                    f"(type={result['duplicate_type']})"
                )
        
        logger.info(
            f"중복 제거 완료: {len(items)} → {len(unique_items)} "
            f"({len(items) - len(unique_items)} 제거)"
        )
        
        return unique_items
    
    def get_statistics(self) -> Dict:
        """통계 반환"""
        return {
            **self.stats,
            'duplicate_rate': (
                self.stats['duplicates_found'] / 
                max(self.stats['total_checked'], 1) * 100
            ),
            'near_duplicate_rate': (
                self.stats['near_duplicates_found'] / 
                max(self.stats['total_checked'], 1) * 100
            ),
            'unique_rate': (
                self.stats['unique_items'] / 
                max(self.stats['total_checked'], 1) * 100
            ),
            'bloom_filter_size': self.url_bloom.size,
            'simhash_index_size': len(self.simhash_index)
        }
    
    def clear_cache(self):
        """캐시 초기화 (메모리 관리)"""
        # URL 캐시는 일정 크기 이상일 때만 정리
        if len(self.url_cache) > 100000:
            # 오래된 항목 제거 (간단히 절반만 유지)
            keep_size = 50000
            self.url_cache = set(list(self.url_cache)[-keep_size:])
            logger.info(f"URL 캐시 정리: {keep_size}개 유지")
        
        # SimHash 인덱스도 크기 제한
        if len(self.simhash_index) > 50000:
            # 오래된 항목 제거
            keep_size = 25000
            items = list(self.simhash_index.items())
            self.simhash_index = dict(items[-keep_size:])
            logger.info(f"SimHash 인덱스 정리: {keep_size}개 유지")


# 테스트
def test_deduplication_engine():
    """중복 제거 엔진 테스트"""
    
    engine = DeduplicationEngine(similarity_threshold=3)
    
    # 테스트 데이터
    test_items = [
        {
            'url': 'https://www.naver.com/news/article1',
            'title': '국민연금 개혁 방안 발표',
            'content': '정부는 오늘 국민연금 개혁 방안을 발표했습니다. 보험료율을 단계적으로 인상하고...'
        },
        {
            'url': 'https://www.naver.com/news/article1',  # 동일 URL
            'title': '국민연금 개혁 방안 발표',
            'content': '정부는 오늘 국민연금 개혁 방안을 발표했습니다. 보험료율을 단계적으로 인상하고...'
        },
        {
            'url': 'https://www.daum.net/news/article2',
            'title': '국민연금 개혁 방안 발표',  # 동일 제목, 다른 URL
            'content': '정부는 오늘 국민연금 개혁안을 발표했습니다. 보험료율을 점진적으로 올리고...'  # 유사 내용
        },
        {
            'url': 'https://www.joins.com/news/article3',
            'title': '날씨 정보',
            'content': '오늘 전국이 맑은 날씨를 보이겠습니다.'  # 완전히 다른 내용
        },
        {
            'url': 'https://www.NAVER.com/news/article1?param=1&param=2',  # 정규화 필요
            'title': '국민연금 개혁',
            'content': '개혁 내용...'
        }
    ]
    
    print("=" * 60)
    print("중복 제거 엔진 테스트")
    print("=" * 60)
    
    unique_items = []
    
    for i, item in enumerate(test_items, 1):
        print(f"\n항목 {i}: {item['title']}")
        print(f"  URL: {item['url']}")
        
        result = engine.check_duplicate(item)
        
        if result['is_duplicate']:
            print(f"  ❌ 중복: {result['duplicate_type']}")
            if result['similar_id']:
                print(f"  유사 ID: {result['similar_id']}")
        else:
            print(f"  ✅ 고유 항목")
            unique_items.append(item)
    
    # 통계 출력
    stats = engine.get_statistics()
    print(f"\n📊 통계:")
    print(f"  검사: {stats['total_checked']}건")
    print(f"  중복: {stats['duplicates_found']}건 ({stats['duplicate_rate']:.1f}%)")
    print(f"  유사: {stats['near_duplicates_found']}건 ({stats['near_duplicate_rate']:.1f}%)")
    print(f"  고유: {stats['unique_items']}건 ({stats['unique_rate']:.1f}%)")
    
    print(f"\n✅ 최종 고유 항목: {len(unique_items)}개")


if __name__ == "__main__":
    test_deduplication_engine()
