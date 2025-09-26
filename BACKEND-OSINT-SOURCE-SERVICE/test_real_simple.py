#!/usr/bin/env python3
"""
간단한 실제 데이터 크롤링 테스트
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import json
from datetime import datetime

def test_real_data():
    """실제 데이터를 가져오는 간단한 테스트"""
    
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("=" * 60)
    print("🚀 실제 데이터 크롤링 테스트")
    print("=" * 60)
    
    # 1. 국민연금공단 메인 페이지
    print("\n1️⃣ 국민연금공단 메인페이지 테스트...")
    try:
        url = "https://www.nps.or.kr"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제목 추출
        title = soup.find('title')
        print(f"   ✅ 사이트 제목: {title.text if title else 'Not found'}")
        
        # 메인 메뉴 항목들 찾기
        menus = soup.find_all('a', limit=10)
        menu_texts = [m.get_text(strip=True) for m in menus if m.get_text(strip=True)]
        print(f"   ✅ 메뉴 항목 {len(menu_texts)}개 발견")
        
        for i, text in enumerate(menu_texts[:5], 1):
            if text:
                print(f"      - {text}")
        
        results.append({
            'site': '국민연금공단',
            'url': url,
            'status': 'success',
            'title': title.text if title else None,
            'items_found': len(menu_texts)
        })
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        results.append({
            'site': '국민연금공단',
            'url': url,
            'status': 'error',
            'error': str(e)
        })
    
    # 2. 네이버 뉴스에서 '국민연금' 검색
    print("\n2️⃣ 네이버 뉴스 '국민연금' 검색...")
    try:
        url = "https://search.naver.com/search.naver?where=news&query=국민연금&sort=0&photo=0&field=0&pd=1"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 뉴스 제목 찾기
        news_titles = soup.select('a.news_tit')
        
        print(f"   ✅ 뉴스 {len(news_titles)}개 발견")
        
        articles = []
        for i, title in enumerate(news_titles[:5], 1):
            title_text = title.get_text(strip=True)
            link = title.get('href', '')
            print(f"   📰 기사 {i}: {title_text[:60]}...")
            articles.append({
                'title': title_text,
                'url': link
            })
        
        results.append({
            'site': '네이버 뉴스',
            'url': url,
            'status': 'success',
            'query': '국민연금',
            'news_count': len(news_titles),
            'sample_articles': articles
        })
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        results.append({
            'site': '네이버 뉴스',
            'status': 'error',
            'error': str(e)
        })
    
    # 3. 구글 뉴스 RSS (한국)
    print("\n3️⃣ 구글 뉴스 RSS (국민연금)...")
    try:
        url = "https://news.google.com/rss/search?q=국민연금+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        
        print(f"   ✅ RSS 항목 {len(feed.entries)}개 발견")
        
        rss_items = []
        for i, entry in enumerate(feed.entries[:5], 1):
            print(f"   📄 뉴스 {i}: {entry.title[:60]}...")
            print(f"      출처: {entry.source.title if hasattr(entry, 'source') else 'Unknown'}")
            print(f"      링크: {entry.link[:50]}...")
            rss_items.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', 'Unknown')
            })
        
        results.append({
            'site': '구글 뉴스 RSS',
            'url': url,
            'status': 'success',
            'feed_count': len(feed.entries),
            'sample_items': rss_items
        })
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        results.append({
            'site': '구글 뉴스 RSS',
            'status': 'error',
            'error': str(e)
        })
    
    # 4. 연합뉴스 경제 섹션
    print("\n4️⃣ 연합뉴스 경제 섹션...")
    try:
        url = "https://www.yna.co.kr/economy/all"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 기사 제목 찾기
        articles = soup.select('div.news-con strong.news-tl a')
        
        print(f"   ✅ 경제 기사 {len(articles)}개 발견")
        
        article_list = []
        for i, article in enumerate(articles[:5], 1):
            title = article.get_text(strip=True)
            link = article.get('href', '')
            if link and not link.startswith('http'):
                link = f"https://www.yna.co.kr{link}"
            print(f"   📰 기사 {i}: {title[:60]}...")
            article_list.append({
                'title': title,
                'url': link
            })
        
        results.append({
            'site': '연합뉴스',
            'url': url,
            'status': 'success',
            'articles_count': len(articles),
            'sample_articles': article_list
        })
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        results.append({
            'site': '연합뉴스',
            'status': 'error',
            'error': str(e)
        })
    
    # 5. 다음 뉴스 검색
    print("\n5️⃣ 다음 뉴스 '국민연금' 검색...")
    try:
        url = "https://search.daum.net/search?w=news&q=국민연금&DA=YZR&spacing=0"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 뉴스 제목 찾기
        news_items = soup.select('a.tit_main')
        
        print(f"   ✅ 뉴스 {len(news_items)}개 발견")
        
        articles = []
        for i, item in enumerate(news_items[:5], 1):
            title = item.get_text(strip=True)
            link = item.get('href', '')
            print(f"   📰 기사 {i}: {title[:60]}...")
            articles.append({
                'title': title,
                'url': link
            })
        
        results.append({
            'site': '다음 뉴스',
            'url': url,
            'status': 'success',
            'query': '국민연금',
            'news_count': len(news_items),
            'sample_articles': articles
        })
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        results.append({
            'site': '다음 뉴스',
            'status': 'error',
            'error': str(e)
        })
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r.get('status') == 'success')
    total_items = sum(
        r.get('items_found', 0) + 
        r.get('news_count', 0) + 
        r.get('feed_count', 0) + 
        r.get('articles_count', 0)
        for r in results
    )
    
    print(f"✅ 성공: {success_count}/{len(results)} 사이트")
    print(f"📄 총 수집 항목: {total_items}개")
    
    for result in results:
        if result.get('status') == 'success':
            site = result.get('site')
            count = (result.get('items_found', 0) + 
                    result.get('news_count', 0) + 
                    result.get('feed_count', 0) + 
                    result.get('articles_count', 0))
            print(f"   ✅ {site}: {count} items")
        else:
            print(f"   ❌ {result.get('site')}: Failed")
    
    # JSON 파일로 저장
    output_file = f"real_data_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장됨: {output_file}")
    
    # 실제 데이터 검증
    print("\n" + "=" * 60)
    if success_count > 0 and total_items > 0:
        print("✅ 검증 완료: 실제 데이터가 성공적으로 수집되었습니다!")
        print("✅ Mock 데이터 없음 - 모든 데이터는 실제 웹사이트에서 가져온 것입니다.")
    else:
        print("⚠️ 일부 사이트에서 데이터 수집 실패")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    results = test_real_data()
