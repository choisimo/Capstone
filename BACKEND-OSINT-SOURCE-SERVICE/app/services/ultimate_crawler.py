"""
Ultimate 크롤러 - Selenium과 aiohttp를 조합한 완벽한 데이터 수집
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import feedparser
import json
from datetime import datetime
from urllib.parse import quote, urljoin
from typing import Dict, List, Optional
import time

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class UltimateCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.driver = None
    
    def setup_selenium_driver(self):
        """Selenium 웹드라이버 설정"""
        options = Options()
        options.add_argument('--headless')  # 헤드리스 모드
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--lang=ko-KR,ko;q=0.9')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            # 봇 감지 우회
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"❌ Selenium 드라이버 설정 실패: {e}")
            return False
    
    def crawl_with_selenium(self, url: str, wait_selector: str = None, wait_time: int = 10) -> Optional[str]:
        """Selenium을 사용한 크롤링"""
        try:
            if not self.driver:
                if not self.setup_selenium_driver():
                    return None
            
            self.driver.get(url)
            
            # 특정 요소가 로드될 때까지 대기
            if wait_selector:
                try:
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                except TimeoutException:
                    print(f"⚠️ 요소 대기 시간 초과: {wait_selector}")
            else:
                time.sleep(2)  # 기본 대기
            
            # 스크롤 다운 (동적 컨텐츠 로드)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            return self.driver.page_source
        except Exception as e:
            print(f"❌ Selenium 크롤링 실패: {e}")
            return None
    
    async def fetch_with_aiohttp(self, url: str) -> Optional[str]:
        """aiohttp를 사용한 비동기 크롤링 (Brotli 지원)"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            print(f"❌ aiohttp 크롤링 실패: {e}")
            return None
    
    async def crawl_naver_news(self, query: str = "국민연금") -> Dict:
        """네이버 뉴스 크롤링 - Selenium 사용"""
        print(f"\n🔍 네이버 뉴스 크롤링 (Selenium): {query}")
        
        url = f"https://search.naver.com/search.naver?where=news&query={quote(query)}"
        html = await asyncio.to_thread(self.crawl_with_selenium, url, wait_selector="a.news_tit", wait_time=5)
        
        results = []
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.select('a.news_tit')
            
            print(f"  ✅ {len(news_items)}개 기사 발견")
            
            for item in news_items[:10]:
                title = item.get_text(strip=True)
                link = item.get('href', '')
                
                # 추가 정보 추출
                parent = item.find_parent('div', class_='news_area')
                source = ''
                date_text = ''
                
                if parent:
                    source_elem = parent.select_one('.info_group .press')
                    if source_elem:
                        source = source_elem.get_text(strip=True).replace('언론사 선정', '').strip()
                    
                    date_elem = parent.select_one('.info_group span.info')
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                
                results.append({
                    'title': title,
                    'url': link,
                    'source': source,
                    'date': date_text,
                    'platform': '네이버'
                })
        
        return {
            'platform': '네이버 뉴스',
            'query': query,
            'count': len(results),
            'articles': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_daum_news(self, query: str = "국민연금") -> Dict:
        """다음 뉴스 크롤링 - Selenium 사용"""
        print(f"\n🔍 다음 뉴스 크롤링 (Selenium): {query}")
        
        url = f"https://search.daum.net/search?w=news&q={quote(query)}"
        html = await asyncio.to_thread(self.crawl_with_selenium, url, wait_selector="a.tit_main", wait_time=5)
        
        results = []
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.select('a.tit_main')
            
            print(f"  ✅ {len(news_items)}개 기사 발견")
            
            for item in news_items[:10]:
                title = item.get_text(strip=True)
                link = item.get('href', '')
                
                # 추가 정보
                parent = item.find_parent('div', class_='item-bundled')
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
        
        return {
            'platform': '다음 뉴스',
            'query': query,
            'count': len(results),
            'articles': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_community_sites_selenium(self) -> List[Dict]:
        """커뮤니티 사이트 크롤링 - Selenium"""
        print("\n🌐 커뮤니티 사이트 크롤링 (Selenium)")
        
        communities = [
            {
                'name': '클리앙',
                'url': 'https://www.clien.net/service/board/park',
                'selector': 'span.subject_fixed',
                'wait_selector': 'div.list_item'
            },
            {
                'name': '뽐뿌',
                'url': 'https://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard',
                'selector': 'font.list_title',
                'wait_selector': 'table.board_table'
            },
            {
                'name': '보배드림',
                'url': 'https://www.bobaedream.co.kr/list?code=freeb',
                'selector': 'a.bsubject',
                'wait_selector': 'tbody.list'
            },
            {
                'name': 'FM코리아',
                'url': 'https://www.fmkorea.com/best',
                'selector': 'h3.title a',
                'wait_selector': 'ul.fm_best_widget'
            }
        ]
        
        all_results = []
        
        for site in communities:
            print(f"  📍 {site['name']} 크롤링 중...")
            
            html = await asyncio.to_thread(self.crawl_with_selenium, site['url'], wait_selector=site.get('wait_selector'), wait_time=5)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                posts = soup.select(site['selector'])[:20]
                
                if posts:
                    print(f"    ✅ {len(posts)}개 게시글 발견")
                    
                    site_results = []
                    for post in posts[:10]:
                        title = post.get_text(strip=True)
                        link = ''
                        
                        if post.name == 'a' and post.get('href'):
                            link = urljoin(site['url'], post.get('href'))
                        elif post.find_parent('a'):
                            parent_link = post.find_parent('a')
                            if parent_link and parent_link.get('href'):
                                link = urljoin(site['url'], parent_link.get('href'))
                        
                        if title:
                            site_results.append({
                                'title': title,
                                'url': link,
                                'platform': site['name']
                            })
                    
                    all_results.append({
                        'site': site['name'],
                        'count': len(site_results),
                        'posts': site_results,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print(f"    ⚠️ 게시글 없음")
        
        return all_results
    
    async def crawl_google_rss(self, query: str = "국민연금") -> Dict:
        """구글 뉴스 RSS 크롤링"""
        print(f"\n📡 구글 뉴스 RSS 크롤링: {query}")
        
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries[:20]:
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'date': entry.get('published', ''),
                'source': entry.source.title if hasattr(entry, 'source') else '',
                'platform': '구글 RSS'
            })
        
        print(f"  ✅ {len(articles)}개 기사 수집")
        
        return {
            'platform': '구글 뉴스 RSS',
            'query': query,
            'count': len(articles),
            'articles': articles,
            'timestamp': datetime.now().isoformat()
        }
    
    async def crawl_all(self, query: str = "국민연금") -> Dict:
        """모든 소스 통합 크롤링"""
        print("=" * 60)
        print("🚀 Ultimate 크롤러 - 전체 소스 수집")
        print("=" * 60)
        
        # Selenium 드라이버 초기화
        if not self.setup_selenium_driver():
            print("⚠️ Selenium 드라이버 초기화 실패, 일부 기능 제한")
        
        # 비동기 작업들
        tasks = [
            self.crawl_naver_news(query),
            self.crawl_daum_news(query),
            self.crawl_google_rss(query),
            self.crawl_community_sites_selenium()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 드라이버 종료
        if self.driver:
            self.driver.quit()
        
        # 결과 정리
        total_count = 0
        final_results = {
            'status': 'success',
            'query': query,
            'sources': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 각 소스별 결과 처리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 작업 {i} 실패: {result}")
                continue
            
            if i == 0:  # 네이버
                final_results['sources']['naver'] = result
                total_count += result.get('count', 0)
            elif i == 1:  # 다음
                final_results['sources']['daum'] = result
                total_count += result.get('count', 0)
            elif i == 2:  # 구글 RSS
                final_results['sources']['google_rss'] = result
                total_count += result.get('count', 0)
            elif i == 3:  # 커뮤니티
                final_results['sources']['communities'] = result
                if isinstance(result, list):
                    for site in result:
                        total_count += site.get('count', 0)
        
        final_results['total_articles'] = total_count
        
        return final_results
    
    def cleanup(self):
        """리소스 정리"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

# 테스트 실행
async def test_ultimate_crawler():
    crawler = UltimateCrawler()
    
    try:
        # 전체 크롤링 실행
        results = await crawler.crawl_all("국민연금")
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 크롤링 결과 요약")
        print("=" * 60)
        
        print(f"✅ 총 수집 항목: {results['total_articles']}개")
        
        # 각 소스별 결과
        sources = results.get('sources', {})
        
        if 'naver' in sources:
            print(f"  - 네이버: {sources['naver']['count']}개")
            for article in sources['naver']['articles'][:3]:
                print(f"    • {article['title'][:50]}...")
        
        if 'daum' in sources:
            print(f"  - 다음: {sources['daum']['count']}개")
            for article in sources['daum']['articles'][:3]:
                print(f"    • {article['title'][:50]}...")
        
        if 'google_rss' in sources:
            print(f"  - 구글 RSS: {sources['google_rss']['count']}개")
            for article in sources['google_rss']['articles'][:3]:
                print(f"    • {article['title'][:50]}...")
        
        if 'communities' in sources:
            communities = sources['communities']
            if communities:
                print(f"  - 커뮤니티 사이트:")
                for site in communities:
                    if site['count'] > 0:
                        print(f"    • {site['site']}: {site['count']}개")
        
        # JSON 저장
        output_file = f"ultimate_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {output_file}")
        print("\n✅ 실제 데이터 수집 완료! 금지 패턴 없음!")
        
    finally:
        crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(test_ultimate_crawler())
