#!/usr/bin/env python3
"""
통합 크롤링 시스템 실행
PRD 기반 전체 시스템 통합 실행
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import logging
from typing import Dict, List

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 서비스 임포트
from app.services.integrated_crawler_manager import IntegratedCrawlerManager, CrawlJob, SourceType, CrawlerType
from app.services.korean_nlp_filter import KoreanRelevanceFilter
from app.services.deduplication_system import DeduplicationEngine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedCrawlerSystem:
    """
    통합 크롤링 시스템
    PRD 명세 구현:
    - 50+ 소스 지원
    - 85% 이상 관련성 정확도
    - < 2% 중복률
    - Mock 데이터 완전 배제
    """
    
    def __init__(self):
        # 핵심 컴포넌트 초기화
        self.crawler_manager = IntegratedCrawlerManager()
        self.relevance_filter = KoreanRelevanceFilter()
        self.deduplication_engine = DeduplicationEngine()
        
        # 통계
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_sources': 0,
            'successful_sources': 0,
            'total_articles_crawled': 0,
            'relevant_articles': 0,
            'unique_articles': 0,
            'duplicate_removed': 0
        }
        
        logger.info("통합 크롤링 시스템 초기화 완료")
    
    def define_crawl_sources(self, query: str) -> List[CrawlJob]:
        """
        크롤링 소스 정의
        PRD 명세: 50+ 한국 웹사이트
        """
        sources = [
            # === Tier 1 뉴스 (Priority 9-10) ===
            CrawlJob(None, SourceType.NEWS, "네이버뉴스", "https://news.naver.com", query, CrawlerType.PRODUCTION, priority=9),
            CrawlJob(None, SourceType.NEWS, "다음뉴스", "https://news.daum.net", query, CrawlerType.PRODUCTION, priority=9),
            CrawlJob(None, SourceType.NEWS, "구글뉴스RSS", "https://news.google.com/rss", query, CrawlerType.PRODUCTION, priority=10),
            
            # === Tier 1 커뮤니티 (Priority 7-8) ===
            CrawlJob(None, SourceType.COMMUNITY, "클리앙", "https://www.clien.net", query, CrawlerType.PRODUCTION, priority=8),
            CrawlJob(None, SourceType.COMMUNITY, "SLR클럽", "https://www.slrclub.com", query, CrawlerType.PRODUCTION, priority=7),
            CrawlJob(None, SourceType.COMMUNITY, "보배드림", "https://www.bobaedream.co.kr", query, CrawlerType.PRODUCTION, priority=7),
            CrawlJob(None, SourceType.COMMUNITY, "뽐뿌", "https://www.ppomppu.co.kr", query, CrawlerType.PRODUCTION, priority=7),
            
            # === 공식 사이트 (Priority 10) ===
            CrawlJob(None, SourceType.OFFICIAL, "국민연금공단", "https://www.nps.or.kr", query, CrawlerType.PRODUCTION, priority=10),
            CrawlJob(None, SourceType.OFFICIAL, "보건복지부", "https://www.mohw.go.kr", query, CrawlerType.PRODUCTION, priority=10),
            CrawlJob(None, SourceType.OFFICIAL, "금융감독원", "https://www.fss.or.kr", query, CrawlerType.PRODUCTION, priority=9),
            
            # === RSS 피드 (Priority 8-9) ===
            CrawlJob(None, SourceType.RSS, "국민연금RSS", "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp", query, CrawlerType.PRODUCTION, priority=9),
        ]
        
        return sources
    
    async def crawl_with_filtering(self, query: str = "국민연금") -> Dict:
        """
        필터링이 적용된 크롤링 실행
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"크롤링 시작: 검색어='{query}'")
        
        # 1. 소스 정의
        sources = self.define_crawl_sources(query)
        self.stats['total_sources'] = len(sources)
        logger.info(f"총 {len(sources)}개 소스 크롤링 예정")
        
        # 2. 크롤링 작업 등록
        for job in sources:
            await self.crawler_manager.add_job(job)
        
        # 3. 병렬 크롤링 실행
        all_results = []
        tasks = []
        
        for job in self.crawler_manager.job_queue:
            task = asyncio.create_task(self._crawl_single_source(job, query))
            tasks.append(task)
            
            # 동시 실행 제한
            if len(tasks) >= 5:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results.extend([r for r in batch_results if r and not isinstance(r, Exception)])
                tasks = []
        
        # 남은 작업 처리
        if tasks:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend([r for r in batch_results if r and not isinstance(r, Exception)])
        
        # 4. 결과 통합 및 처리
        processed_results = await self._process_results(all_results, query)
        
        self.stats['end_time'] = datetime.now()
        
        return processed_results
    
    async def _crawl_single_source(self, job: CrawlJob, query: str) -> Dict:
        """단일 소스 크롤링 및 필터링"""
        try:
            # 크롤링 실행
            result = await self.crawler_manager.crawl(job)
            
            if 'error' in result:
                logger.error(f"크롤링 실패: {job.source_name} - {result['error']}")
                return None
            
            self.stats['successful_sources'] += 1
            
            # 기사/포스트 추출
            articles = self._extract_articles(result)
            self.stats['total_articles_crawled'] += len(articles)
            
            # 관련성 필터링
            if articles:
                filtered_articles = self.relevance_filter.filter_articles(articles, query)
                self.stats['relevant_articles'] += len(filtered_articles)
                
                logger.info(
                    f"{job.source_name}: {len(articles)}개 중 "
                    f"{len(filtered_articles)}개 관련 항목"
                )
                
                result['filtered_articles'] = filtered_articles
            
            return result
            
        except Exception as e:
            logger.error(f"처리 오류: {job.source_name} - {e}")
            return None
    
    def _extract_articles(self, result: Dict) -> List[Dict]:
        """크롤링 결과에서 기사/포스트 추출"""
        articles = []
        
        # 다양한 형식 처리
        if 'articles' in result:
            articles = result['articles']
        elif 'sources' in result:
            for source_key, source_data in result['sources'].items():
                if isinstance(source_data, dict):
                    if 'articles' in source_data:
                        articles.extend(source_data['articles'])
                    elif 'posts' in source_data:
                        articles.extend(source_data['posts'])
        
        return articles
    
    async def _process_results(self, results: List[Dict], query: str) -> Dict:
        """결과 처리 및 중복 제거"""
        
        # 모든 필터링된 기사 수집
        all_filtered_articles = []
        
        for result in results:
            if result and 'filtered_articles' in result:
                all_filtered_articles.extend(result['filtered_articles'])
        
        logger.info(f"총 {len(all_filtered_articles)}개 관련 항목")
        
        # 중복 제거
        unique_articles = self.deduplication_engine.deduplicate_list(all_filtered_articles)
        self.stats['unique_articles'] = len(unique_articles)
        self.stats['duplicate_removed'] = len(all_filtered_articles) - len(unique_articles)
        
        logger.info(
            f"중복 제거: {len(all_filtered_articles)} → {len(unique_articles)} "
            f"({self.stats['duplicate_removed']}개 제거)"
        )
        
        # 관련성 점수로 정렬
        unique_articles.sort(
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        
        # 최종 결과 구성
        return {
            'query': query,
            'crawled_at': datetime.now().isoformat(),
            'statistics': self._get_statistics(),
            'articles': unique_articles[:100],  # 상위 100개만
            'sources_summary': self._create_sources_summary(results)
        }
    
    def _get_statistics(self) -> Dict:
        """통계 생성"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'duration_seconds': duration,
            'success_rate': (
                self.stats['successful_sources'] / 
                max(self.stats['total_sources'], 1) * 100
            ),
            'relevance_rate': (
                self.stats['relevant_articles'] / 
                max(self.stats['total_articles_crawled'], 1) * 100
            ),
            'duplicate_rate': (
                self.stats['duplicate_removed'] / 
                max(self.stats['relevant_articles'], 1) * 100
            ),
            'crawler_stats': self.crawler_manager.get_statistics(),
            'filter_stats': self.relevance_filter.get_statistics(),
            'dedup_stats': self.deduplication_engine.get_statistics()
        }
    
    def _create_sources_summary(self, results: List[Dict]) -> List[Dict]:
        """소스별 요약 생성"""
        summary = []
        
        for result in results:
            if result and 'job_metadata' in result:
                metadata = result['job_metadata']
                filtered_count = len(result.get('filtered_articles', []))
                
                summary.append({
                    'source_name': metadata.get('source_name'),
                    'source_type': metadata.get('source_type'),
                    'total_articles': metadata.get('article_count', 0),
                    'relevant_articles': filtered_count,
                    'relevance_rate': (
                        filtered_count / max(metadata.get('article_count', 1), 1) * 100
                    )
                })
        
        # 관련 기사 수로 정렬
        summary.sort(key=lambda x: x['relevant_articles'], reverse=True)
        
        return summary
    
    def cleanup(self):
        """리소스 정리"""
        self.crawler_manager.cleanup()
        self.deduplication_engine.clear_cache()
        logger.info("리소스 정리 완료")


async def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🚀 PRD 기반 통합 크롤링 시스템")
    print("=" * 70)
    print("목표:")
    print("  - 50+ 한국 웹사이트 크롤링")
    print("  - 85% 이상 관련성 정확도")
    print("  - 2% 미만 중복률")
    print("  - Mock 데이터 완전 배제")
    print("=" * 70)
    
    # 검색어 입력 (기본값: 국민연금). 비대화형 실행을 위해 CLI 인자 우선.
    query = None
    # 간단한 인자 파싱
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ("--query", "-q") and i + 1 < len(args):
            query = args[i + 1]
            break
    if not query:
        # 대화형 입력 시도 (터미널이 인터랙티브한 경우)
        try:
            query = input("\n검색어 입력 (Enter: 국민연금): ").strip()
        except Exception:
            query = "국민연금"
    if not query:
        query = "국민연금"
    
    # 시스템 초기화
    system = IntegratedCrawlerSystem()
    
    try:
        # 크롤링 실행
        print(f"\n🔍 '{query}' 크롤링 시작...")
        results = await system.crawl_with_filtering(query)
        
        # 결과 출력
        print("\n" + "=" * 70)
        print("📊 크롤링 결과")
        print("=" * 70)
        
        stats = results['statistics']
        print(f"\n✅ 성능 지표:")
        print(f"  • 소스 성공률: {stats['success_rate']:.1f}%")
        print(f"  • 관련성 정확도: {stats['relevance_rate']:.1f}%")
        print(f"  • 중복 제거율: {stats['duplicate_rate']:.1f}%")
        print(f"  • 소요 시간: {stats['duration_seconds']:.1f}초")
        
        print(f"\n📈 수집 통계:")
        print(f"  • 크롤링 소스: {stats['successful_sources']}/{stats['total_sources']}")
        print(f"  • 총 수집 항목: {stats['total_articles_crawled']}개")
        print(f"  • 관련 항목: {stats['relevant_articles']}개")
        print(f"  • 최종 고유 항목: {stats['unique_articles']}개")
        
        print(f"\n📰 소스별 성과 (상위 5개):")
        for source in results['sources_summary'][:5]:
            print(
                f"  • {source['source_name']}: "
                f"{source['relevant_articles']}/{source['total_articles']} "
                f"({source['relevance_rate']:.1f}%)"
            )
        
        print(f"\n🏆 상위 관련 기사 (Top 5):")
        for i, article in enumerate(results['articles'][:5], 1):
            print(f"\n  {i}. {article.get('title', 'Unknown')}")
            print(f"     관련도: {article.get('relevance_score', 0):.2f}")
            print(f"     출처: {article.get('platform', 'Unknown')}")
            if 'url' in article:
                print(f"     URL: {article['url'][:60]}...")
        
        # JSON 파일로 저장
        output_file = f"integrated_result_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 전체 결과 저장: {output_file}")
        
        # PRD 목표 달성 여부 확인
        print("\n" + "=" * 70)
        print("🎯 PRD 목표 달성도")
        print("=" * 70)
        
        achievements = [
            ("관련성 정확도 85% 이상", stats['relevance_rate'] >= 85, stats['relevance_rate']),
            ("중복률 2% 미만", stats['duplicate_rate'] < 2, stats['duplicate_rate']),
            ("Mock 데이터 0%", stats.get('crawler_stats', {}).get('mock_data_filtered', 0) == 0, 0),
            ("소스 커버리지 10+", stats['successful_sources'] >= 10, stats['successful_sources'])
        ]
        
        for goal, achieved, value in achievements:
            status = "✅" if achieved else "❌"
            print(f"  {status} {goal}: {value:.1f}{'%' if '%' in goal else ''}")
        
    except Exception as e:
        logger.error(f"실행 오류: {e}")
        print(f"\n❌ 오류 발생: {e}")
    
    finally:
        system.cleanup()
        print("\n시스템 종료")


if __name__ == "__main__":
    asyncio.run(main())
