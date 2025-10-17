"""
고급 크롤링 서비스 - 네이버, 다음, 커뮤니티 사이트 완벽 지원
봇 차단 우회 및 동적 콘텐츠 처리
"""

import asyncio
import aiohttp
from aiohttp import CookieJar
import requests
from bs4 import BeautifulSoup
import feedparser
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote, urljoin, urlparse
import re

class AdvancedCrawler:
    def __init__(self):
        # 다양한 User-Agent 로테이션
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        # 결정론적 로테이션 인덱스
        self._ua_index = 0
        
        # 네이버 전용 헤더
        self.naver_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.naver.com'
        }
        
        # 다음 전용 헤더
        self.daum_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.daum.net',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        }
        
    def next_user_agent(self) -> str:
        """결정론적 User-Agent 로테이션 (random 미사용)"""
        ua = self.user_agents[self._ua_index % len(self.user_agents)]
        self._ua_index += 1
        return ua
    
    async def fetch_with_retry(self, url: str, headers: Dict = None, max_retries: int = 3) -> Optional[str]:
        """재시도 로직을 포함한 비동기 페이지 가져오기"""
        for attempt in range(max_retries):
            try:
                # 요청 간 딜레이 (봇 감지 회피) - 결정론적 지연
                if attempt > 0:
                    await asyncio.sleep(self._deterministic_delay(attempt, url))
                
                cookie_jar = CookieJar()
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(cookie_jar=cookie_jar, timeout=timeout) as session:
                    # 세션 쿠키 설정을 위한 메인 페이지 방문
                    if 'naver.com' in url:
                        await session.get('https://www.naver.com', headers={'User-Agent': self.next_user_agent()})
                    elif 'daum.net' in url:
                        await session.get('https://www.daum.net', headers={'User-Agent': self.next_user_agent()})
                    
                    # 실제 요청
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 403 or response.status == 429:
                            print(f"⚠️ Rate limited or blocked on attempt {attempt + 1}")
                            continue
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                continue
        
        return None

    def _deterministic_delay(self, attempt: int, url: str) -> float:
        """URL과 시도 횟수 기반 결정론적 지연(1.0~3.0초)"""
        seed = f"{url}:{attempt}"
        h = hashlib.sha256(seed.encode()).digest()
        val = int.from_bytes(h[:2], 'big') / 65535.0  # 0..1
        return 1.0 + 2.0 * val
    
    async def crawl_naver_news(self, query: str = "국민연금") -> Dict:
        """네이버 뉴스 크롤링 - 개선된 방법"""
        print(f"\n🔍 네이버 뉴스 크롤링: {query}")
        
        # URL 인코딩
        encoded_query = quote(query)
        
        # 여러 접근 방법 시도
        strategies = [
            {
                'name': '네이버 뉴스 검색 API 스타일',
                'url': f'https://search.naver.com/search.naver?where=news&sm=tab_jum&query={encoded_query}',
                'selector': 'a.news_tit'
            },
            {
                'name': '네이버 뉴스 탭',
                'url': f'https://search.naver.com/search.naver?where=news&query={encoded_query}&sm=tab_opt&sort=0&photo=0&field=0&pd=0&ds=&de=&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=&is_sug_officeid=0',
                'selector': 'a.news_tit'
            },
            {
                'name': '네이버 통합검색',
                'url': f'https://search.naver.com/search.naver?query={encoded_query}',
                'selector': '.news_wrap a.news_tit'
            }
        ]
        
        results = []
        
        for strategy in strategies:
            headers = self.naver_headers.copy()
            headers['User-Agent'] = self.next_user_agent()
            
            html = await self.fetch_with_retry(strategy['url'], headers)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.select(strategy['selector'])
                
                if news_items:
                    print(f"  ✅ {strategy['name']}: {len(news_items)}개 기사 발견")
                    
                    for item in news_items[:10]:
                        title = item.get_text(strip=True)
                        link = item.get('href', '')
                        
                        # 추가 정보 추출
                        parent = item.find_parent(['div', 'li'])
                        source = ''
                        date_text = ''
                        
                        if parent:
                            source_elem = parent.select_one('.info_group .press')
                            if source_elem:
                                source = source_elem.get_text(strip=True)
                            
                            date_elem = parent.select_one('.info_group .info')
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                        
                        results.append({
                            'title': title,
                            'url': link,
                            'source': source,
                            'date': date_text,
                            'platform': '네이버'
                        })
                    
                    break  # 성공하면 중단
                else:
                    print(f"  ⚠️ {strategy['name']}: 결과 없음")
        
        return {
            'platform': '네이버 뉴스',
            'query': query,
            'count': len(results),
            'articles': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_daum_news(self, query: str = "국민연금") -> Dict:
        """다음 뉴스 크롤링 - 개선된 방법"""
        print(f"\n🔍 다음 뉴스 크롤링: {query}")
        
        encoded_query = quote(query)
        
        strategies = [
            {
                'name': '다음 뉴스 검색',
                'url': f'https://search.daum.net/search?w=news&nil_search=btn&DA=NTB&enc=utf8&cluster=y&cluster_page=1&q={encoded_query}',
                'selector': 'a.f_link_b'
            },
            {
                'name': '다음 뉴스 최신순',
                'url': f'https://search.daum.net/search?w=news&DA=STC&enc=utf8&cluster=y&cluster_page=1&q={encoded_query}',
                'selector': 'a.tit_main'
            }
        ]
        
        results = []
        
        for strategy in strategies:
            headers = self.daum_headers.copy()
            headers['User-Agent'] = self.next_user_agent()
            
            html = await self.fetch_with_retry(strategy['url'], headers)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.select(strategy['selector'])
                
                if news_items:
                    print(f"  ✅ {strategy['name']}: {len(news_items)}개 기사 발견")
                    
                    for item in news_items[:10]:
                        title = item.get_text(strip=True)
                        link = item.get('href', '')
                        
                        # 추가 정보 추출
                        parent = item.find_parent(['div', 'li'])
                        source = ''
                        date_text = ''
                        
                        if parent:
                            source_elem = parent.select_one('.f_nb')
                            if source_elem:
                                source = source_elem.get_text(strip=True)
                            
                            date_elem = parent.select_one('.f_nb.date')
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                        
                        results.append({
                            'title': title,
                            'url': link,
                            'source': source,
                            'date': date_text,
                            'platform': '다음'
                        })
                    
                    break
                else:
                    print(f"  ⚠️ {strategy['name']}: 결과 없음")
        
        return {
            'platform': '다음 뉴스',
            'query': query,
            'count': len(results),
            'articles': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_community_sites(self) -> List[Dict]:
        """커뮤니티 사이트 크롤링"""
        print("\n🌐 커뮤니티 사이트 크롤링")
        
        communities = [
            {
                'name': '클리앙',
                'url': 'https://www.clien.net/service/board/park',
                'selector': 'span.subject_fixed',
                'link_selector': 'a.list_subject',
                'platform': 'clien'
            },
            {
                'name': '뽐뿌',
                'url': 'https://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard',
                'selector': 'font.list_title',
                'link_selector': 'a[href*="view.php"]',
                'platform': 'ppomppu'
            },
            {
                'name': 'MLBPark',
                'url': 'http://mlbpark.donga.com/mp/b.php?b=bullpen',
                'selector': 'a.bullpenbox',
                'link_selector': 'a.bullpenbox',
                'platform': 'mlbpark'
            },
            {
                'name': 'FM코리아',
                'url': 'https://www.fmkorea.com/index.php?mid=best',
                'selector': 'h3.title a',
                'link_selector': 'h3.title a',
                'platform': 'fmkorea'
            },
            {
                'name': '루리웹',
                'url': 'https://bbs.ruliweb.com/best/board/300143',
                'selector': 'a.subject',
                'link_selector': 'a.subject',
                'platform': 'ruliweb'
            }
        ]
        
        all_results = []
        
        for site in communities:
            print(f"  📍 {site['name']} 크롤링 중...")
            
            headers = {
                'User-Agent': self.next_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
            
            # 각 사이트별 특별 처리
            if site['platform'] == 'clien':
                headers['Referer'] = 'https://www.clien.net'
            elif site['platform'] == 'ppomppu':
                headers['Referer'] = 'https://www.ppomppu.co.kr'
            
            html = await self.fetch_with_retry(site['url'], headers)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                posts = soup.select(site['selector'])[:20]
                
                if posts:
                    print(f"    ✅ {len(posts)}개 게시글 발견")
                    
                    site_results = []
                    for post in posts[:10]:
                        title = post.get_text(strip=True)
                        
                        # 링크 추출
                        if site['link_selector'] != site['selector']:
                            link_elem = post.find_parent().select_one(site['link_selector'])
                        else:
                            link_elem = post
                        
                        link = ''
                        if link_elem and link_elem.get('href'):
                            link = urljoin(site['url'], link_elem.get('href'))
                        
                        site_results.append({
                            'title': title,
                            'url': link,
                            'platform': site['name'],
                            'source_url': site['url']
                        })
                    
                    all_results.append({
                        'site': site['name'],
                        'count': len(site_results),
                        'posts': site_results,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print(f"    ⚠️ 게시글을 찾을 수 없음")
            else:
                print(f"    ❌ 페이지 로드 실패")
        
        return all_results
    
    async def crawl_naver_api(self, query: str = "국민연금") -> Dict:
        """네이버 검색 API 스타일 접근 (공식 API 아님)"""
        print(f"\n🔧 네이버 API 스타일 크롤링: {query}")
        
        # 모바일 버전 시도 (더 간단한 구조)
        mobile_url = f"https://m.search.naver.com/search.naver?where=m_news&query={quote(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        html = await self.fetch_with_retry(mobile_url, headers)
        
        results = []
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 모바일 뉴스 선택자
            news_items = soup.select('.news_wrap .bx')
            
            if news_items:
                print(f"  ✅ 모바일 버전에서 {len(news_items)}개 기사 발견")
                
                for item in news_items[:10]:
                    title_elem = item.select_one('.news_tit')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        source_elem = item.select_one('.info_group .press')
                        source = source_elem.get_text(strip=True) if source_elem else ''
                        
                        date_elem = item.select_one('.info_group .info')
                        date_text = date_elem.get_text(strip=True) if date_elem else ''
                        
                        results.append({
                            'title': title,
                            'url': link,
                            'source': source,
                            'date': date_text,
                            'platform': '네이버 모바일'
                        })
        
        return {
            'platform': '네이버 API 스타일',
            'query': query,
            'count': len(results),
            'articles': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_all_sources(self, query: str = "국민연금") -> Dict:
        """모든 소스 통합 크롤링"""
        print("=" * 60)
        print("🚀 전체 소스 크롤링 시작")
        print("=" * 60)
        
        tasks = [
            self.crawl_naver_news(query),
            self.crawl_naver_api(query),
            self.crawl_daum_news(query),
            self.crawl_community_sites()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 구글 뉴스 RSS (이미 작동 확인됨)
        google_rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(google_rss_url)
        
        google_results = {
            'platform': '구글 뉴스 RSS',
            'query': query,
            'count': len(feed.entries),
            'articles': [
                {
                    'title': entry.title,
                    'url': entry.link,
                    'date': entry.get('published', ''),
                    'source': entry.source.title if hasattr(entry, 'source') else '',
                    'platform': '구글 RSS'
                }
                for entry in feed.entries[:10]
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # 통합 결과
        total_articles = sum(
            r.get('count', 0) if not isinstance(r, list) else sum(s.get('count', 0) for s in r)
            for r in results
        ) + google_results['count']
        
        return {
            'status': 'success',
            'total_articles': total_articles,
            'sources': {
                'naver': results[0],
                'naver_mobile': results[1],
                'daum': results[2],
                'communities': results[3],
                'google_rss': google_results
            },
            'timestamp': datetime.now().isoformat()
        }

# 테스트 실행
async def test_advanced_crawler():
    crawler = AdvancedCrawler()
    
    # 개별 테스트
    print("\n" + "="*60)
    print("개별 소스 테스트")
    print("="*60)
    
    # 네이버 테스트
    naver_results = await crawler.crawl_naver_news("국민연금")
    print(f"\n✅ 네이버: {naver_results['count']}개 기사")
    for article in naver_results['articles'][:3]:
        print(f"  - {article['title'][:50]}...")
    
    # 다음 테스트
    daum_results = await crawler.crawl_daum_news("국민연금")
    print(f"\n✅ 다음: {daum_results['count']}개 기사")
    for article in daum_results['articles'][:3]:
        print(f"  - {article['title'][:50]}...")
    
    # 커뮤니티 테스트
    community_results = await crawler.crawl_community_sites()
    print(f"\n✅ 커뮤니티 사이트: {len(community_results)}개 사이트")
    for site in community_results:
        if site['count'] > 0:
            print(f"  - {site['site']}: {site['count']}개 게시글")
    
    # 전체 통합 테스트
    print("\n" + "="*60)
    print("통합 크롤링 테스트")
    print("="*60)
    
    all_results = await crawler.crawl_all_sources("국민연금")
    
    print(f"\n📊 총 수집 결과:")
    print(f"  - 전체 기사/게시글: {all_results['total_articles']}개")
    print(f"  - 네이버: {all_results['sources']['naver']['count']}개")
    print(f"  - 네이버 모바일: {all_results['sources']['naver_mobile']['count']}개")
    print(f"  - 다음: {all_results['sources']['daum']['count']}개")
    print(f"  - 구글 RSS: {all_results['sources']['google_rss']['count']}개")
    
    communities = all_results['sources']['communities']
    if communities:
        print(f"  - 커뮤니티: {len(communities)}개 사이트")
    
    # JSON 파일로 저장
    output_file = f"advanced_crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장: {output_file}")
    
    return all_results

if __name__ == "__main__":
    asyncio.run(test_advanced_crawler())
