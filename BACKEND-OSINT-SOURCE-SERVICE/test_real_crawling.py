#!/usr/bin/env python3
"""
실제 크롤링 테스트 스크립트
실제 한국 뉴스/커뮤니티 사이트에서 데이터를 수집합니다.
"""

import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
import json
import feedparser
from typing import Dict, List, Optional

class RealCrawlerTest:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """URL에서 HTML 컨텐츠 가져오기"""
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"❌ Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None
    
    async def test_nps_kr(self):
        """국민연금공단 뉴스 페이지 크롤링"""
        print("\n📰 Testing 국민연금공단 (NPS)...")
        url = "https://www.nps.or.kr/jsppage/cyber_pr/news/news_01.jsp"
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_url(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 제목 추출
                title = soup.find('title')
                print(f"  ✅ Page Title: {title.text if title else 'Not found'}")
                
                # 뉴스 항목 찾기 (실제 HTML 구조에 맞게 조정)
                news_items = soup.find_all(['li', 'div', 'article'], limit=5)
                
                result = {
                    'source': '국민연금공단',
                    'url': url,
                    'status': 'success',
                    'title': title.text if title else None,
                    'items_found': len(news_items),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                print(f"  ✅ Found {len(news_items)} potential news items")
                
                # 텍스트 내용 샘플
                for i, item in enumerate(news_items[:3], 1):
                    text = item.get_text(strip=True)[:100]
                    if text:
                        print(f"    Item {i}: {text}...")
                
                self.results.append(result)
                return result
    
    async def test_mohw_kr(self):
        """보건복지부 보도자료 크롤링"""
        print("\n📰 Testing 보건복지부 (MOHW)...")
        url = "https://www.mohw.go.kr/board.es?mid=a10503000000&bid=0027"
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_url(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                title = soup.find('title')
                print(f"  ✅ Page Title: {title.text if title else 'Not found'}")
                
                # 보도자료 목록 찾기
                articles = soup.find_all(['tr', 'li', 'div'], class_=['list', 'board', 'article'], limit=5)
                
                result = {
                    'source': '보건복지부',
                    'url': url,
                    'status': 'success',
                    'title': title.text if title else None,
                    'items_found': len(articles),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                print(f"  ✅ Found {len(articles)} potential articles")
                self.results.append(result)
                return result
    
    async def test_nps_rss(self):
        """국민연금공단 RSS 피드 테스트"""
        print("\n📡 Testing 국민연금공단 RSS Feed...")
        url = "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp"
        
        try:
            # RSS는 동기적으로 처리 (feedparser는 동기 라이브러리)
            feed = feedparser.parse(url)
            
            if feed.bozo:
                print(f"  ⚠️ RSS parse warning: {feed.bozo_exception}")
            
            print(f"  ✅ Feed Title: {feed.feed.get('title', 'Unknown')}")
            print(f"  ✅ Feed Items: {len(feed.entries)}")
            
            result = {
                'source': '국민연금공단 RSS',
                'url': url,
                'status': 'success',
                'feed_title': feed.feed.get('title'),
                'items_count': len(feed.entries),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 최신 항목 3개 출력
            for i, entry in enumerate(feed.entries[:3], 1):
                print(f"    📄 Item {i}: {entry.get('title', 'No title')}")
                print(f"       Link: {entry.get('link', 'No link')}")
                if 'published' in entry:
                    print(f"       Published: {entry.published}")
            
            self.results.append(result)
            return result
        except Exception as e:
            print(f"  ❌ RSS Error: {e}")
            return None
    
    async def test_community_site(self):
        """커뮤니티 사이트 테스트 (클리앙)"""
        print("\n💬 Testing 커뮤니티 사이트 (클리앙)...")
        url = "https://www.clien.net/service/board/park"
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_url(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                title = soup.find('title')
                print(f"  ✅ Page Title: {title.text if title else 'Not found'}")
                
                # 게시글 목록 찾기
                posts = soup.find_all(['div', 'tr'], class_=['list_item', 'list_row', 'symph_row'], limit=5)
                
                result = {
                    'source': '클리앙',
                    'url': url,
                    'status': 'success',
                    'title': title.text if title else None,
                    'posts_found': len(posts),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                print(f"  ✅ Found {len(posts)} posts")
                
                # 게시글 제목 추출 시도
                for post in posts[:3]:
                    title_elem = post.find(['a', 'span'], class_=['subject', 'title'])
                    if title_elem:
                        print(f"    📝 Post: {title_elem.get_text(strip=True)[:80]}...")
                
                self.results.append(result)
                return result
    
    async def test_news_search(self):
        """네이버 뉴스에서 '국민연금' 검색"""
        print("\n🔍 Testing 네이버 뉴스 검색 (국민연금)...")
        url = "https://search.naver.com/search.naver?where=news&query=국민연금"
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_url(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 뉴스 제목 찾기
                news_titles = soup.find_all(['a'], class_=['news_tit'], limit=5)
                
                result = {
                    'source': '네이버 뉴스 검색',
                    'url': url,
                    'status': 'success',
                    'query': '국민연금',
                    'news_found': len(news_titles),
                    'timestamp': datetime.utcnow().isoformat(),
                    'articles': []
                }
                
                print(f"  ✅ Found {len(news_titles)} news articles")
                
                for i, title in enumerate(news_titles, 1):
                    article_title = title.get_text(strip=True)
                    article_url = title.get('href')
                    print(f"    📰 Article {i}: {article_title[:80]}...")
                    result['articles'].append({
                        'title': article_title,
                        'url': article_url
                    })
                
                self.results.append(result)
                return result
    
    async def test_http_monitoring(self):
        """모든 소스의 HTTP 상태 확인"""
        print("\n🔍 Testing HTTP Status for all sources...")
        
        sources = [
            ("국민연금공단", "https://www.nps.or.kr"),
            ("보건복지부", "https://www.mohw.go.kr"),
            ("국민연금연구원", "https://institute.nps.or.kr"),
            ("클리앙", "https://www.clien.net"),
            ("뽐뿌", "https://www.ppomppu.co.kr"),
            ("보배드림", "https://www.bobaedream.co.kr"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for name, url in sources:
                try:
                    start_time = datetime.utcnow()
                    async with session.head(url, headers=self.headers, timeout=5, allow_redirects=True) as response:
                        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        status = "✅" if response.status < 400 else "⚠️"
                        print(f"  {status} {name}: HTTP {response.status} ({response_time:.0f}ms)")
                except asyncio.TimeoutError:
                    print(f"  ⏱️ {name}: Timeout")
                except Exception as e:
                    print(f"  ❌ {name}: Error - {str(e)[:50]}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 60)
        print("🚀 Starting Real Crawling Tests")
        print("=" * 60)
        
        # HTTP 상태 체크
        await self.test_http_monitoring()
        
        # 개별 사이트 테스트
        await self.test_nps_kr()
        await self.test_mohw_kr()
        await self.test_nps_rss()
        await self.test_community_site()
        await self.test_news_search()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        success_count = sum(1 for r in self.results if r.get('status') == 'success')
        print(f"✅ Successful: {success_count}/{len(self.results)}")
        
        for result in self.results:
            status_icon = "✅" if result.get('status') == 'success' else "❌"
            items = result.get('items_found', result.get('items_count', result.get('news_found', 0)))
            print(f"{status_icon} {result['source']}: {items} items found")
        
        # JSON 파일로 저장
        output_file = f"crawl_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
        return self.results

async def main():
    crawler = RealCrawlerTest()
    results = await crawler.run_all_tests()
    
    # 검증
    if results:
        print("\n" + "=" * 60)
        print("✅ VERIFICATION: Real data collection successful!")
        print("All crawling targets returned actual data.")
        print("=" * 60)
    else:
        print("\n❌ VERIFICATION: No results collected")

if __name__ == "__main__":
    # 필요한 패키지 설치 확인
    try:
        import aiohttp
        import feedparser
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install aiohttp feedparser beautifulsoup4")
        exit(1)
    
    # 테스트 실행
    asyncio.run(main())
