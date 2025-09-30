#!/usr/bin/env python3
"""
실제 데이터 수집 스크립트
국민연금 관련 실제 데이터를 다양한 소스에서 수집합니다.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import feedparser
import hashlib

# 데이터 수집 소스 설정
DATA_SOURCES = {
    "rss_feeds": [
        {
            "name": "국민연금공단 뉴스",
            "url": "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp",
            "category": "official"
        },
        {
            "name": "보건복지부 보도자료",
            "url": "https://www.mohw.go.kr/rss/news.xml",
            "category": "government"
        },
        {
            "name": "연합뉴스 경제",
            "url": "https://www.yonhapnewstv.co.kr/category/news/economy/feed/",
            "category": "news"
        },
        {
            "name": "한겨레 경제",
            "url": "http://www.hani.co.kr/rss/economy/",
            "category": "news"
        },
        {
            "name": "조선일보 경제",
            "url": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
            "category": "news"
        }
    ],
    "reddit": {
        "subreddits": ["korea", "hanguk", "Korean", "Living_in_Korea"],
        "keywords": ["국민연금", "연금", "pension", "retirement", "노후"]
    },
    "news_comments": [
        {
            "name": "네이버 뉴스",
            "search_url": "https://search.naver.com/search.naver?where=news&query=국민연금",
            "category": "portal"
        },
        {
            "name": "다음 뉴스",
            "search_url": "https://search.daum.net/search?w=news&q=국민연금",
            "category": "portal"
        }
    ]
}

def generate_user_id(author: str, platform: str) -> str:
    """사용자 ID 생성"""
    return hashlib.md5(f"{platform}:{author}".encode()).hexdigest()[:16]

def collect_rss_feeds() -> List[Dict[str, Any]]:
    """RSS 피드에서 데이터 수집"""
    collected_data = []
    
    for feed_info in DATA_SOURCES["rss_feeds"]:
        print(f"\n📡 수집 중: {feed_info['name']}")
        print(f"   URL: {feed_info['url']}")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            
            if not feed.entries:
                print(f"   ⚠️ 항목이 없습니다")
                continue
                
            for entry in feed.entries[:20]:  # 각 피드에서 최대 20개
                # 국민연금 관련 항목만 필터링
                if any(keyword in (entry.get('title', '') + entry.get('summary', '')).lower() 
                       for keyword in ['연금', '국민연금', '노후', '퇴직', 'pension', '은퇴']):
                    
                    data = {
                        "id": hashlib.md5(entry.get('link', '').encode()).hexdigest()[:16],
                        "source": feed_info['name'],
                        "category": feed_info['category'],
                        "platform": "rss",
                        "title": entry.get('title', ''),
                        "content": entry.get('summary', '')[:500],
                        "url": entry.get('link', ''),
                        "author": entry.get('author', feed.feed.get('title', 'Unknown')),
                        "author_id": generate_user_id(
                            entry.get('author', feed.feed.get('title', 'Unknown')), 
                            "rss"
                        ),
                        "published_at": entry.get('published', datetime.now().isoformat()),
                        "collected_at": datetime.now().isoformat()
                    }
                    collected_data.append(data)
                    print(f"   ✅ 수집: {data['title'][:50]}...")
                    
        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
            continue
    
    return collected_data

def collect_reddit_data() -> List[Dict[str, Any]]:
    """Reddit에서 데이터 수집 (공개 API)"""
    collected_data = []
    headers = {'User-Agent': 'PensionSentimentBot/1.0'}
    
    for subreddit in DATA_SOURCES["reddit"]["subreddits"]:
        print(f"\n🤖 Reddit 수집: r/{subreddit}")
        
        try:
            # Reddit의 공개 JSON API 사용
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q=pension+OR+연금&limit=25&sort=new"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"   ⚠️ 접근 실패: {response.status_code}")
                continue
                
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                post_data = post['data']
                
                collected_item = {
                    "id": post_data['id'],
                    "source": f"reddit_{subreddit}",
                    "category": "social",
                    "platform": "reddit",
                    "title": post_data.get('title', ''),
                    "content": post_data.get('selftext', '')[:1000],
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "author": post_data.get('author', 'Unknown'),
                    "author_id": generate_user_id(post_data.get('author', 'Unknown'), "reddit"),
                    "score": post_data.get('score', 0),
                    "num_comments": post_data.get('num_comments', 0),
                    "published_at": datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                    "collected_at": datetime.now().isoformat()
                }
                collected_data.append(collected_item)
                print(f"   ✅ 수집: {collected_item['title'][:50]}...")
                
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
            continue
    
    return collected_data

def generate_sample_comments() -> List[Dict[str, Any]]:
    """샘플 댓글 생성은 정책상 비활성화 (REAL DATA ONLY)."""
    return []

def analyze_collected_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """수집된 데이터 분석"""
    analysis = {
        "total_count": len(data),
        "by_platform": {},
        "by_category": {},
        "by_author": {},
        "time_range": {
            "earliest": None,
            "latest": None
        },
        "top_authors": []
    }
    
    # 플랫폼별 집계
    for item in data:
        platform = item.get('platform', 'unknown')
        analysis['by_platform'][platform] = analysis['by_platform'].get(platform, 0) + 1
        
        category = item.get('category', 'unknown')
        analysis['by_category'][category] = analysis['by_category'].get(category, 0) + 1
        
        author = item.get('author', 'Unknown')
        if author not in analysis['by_author']:
            analysis['by_author'][author] = {
                'count': 0,
                'author_id': item.get('author_id'),
                'posts': []
            }
        analysis['by_author'][author]['count'] += 1
        analysis['by_author'][author]['posts'].append(item['id'])
    
    # Top authors
    sorted_authors = sorted(analysis['by_author'].items(), key=lambda x: x[1]['count'], reverse=True)
    analysis['top_authors'] = [
        {
            'name': author,
            'id': info['author_id'],
            'post_count': info['count']
        }
        for author, info in sorted_authors[:10]
    ]
    
    # 시간 범위
    dates = [item.get('published_at', '') for item in data if item.get('published_at')]
    if dates:
        analysis['time_range']['earliest'] = min(dates)
        analysis['time_range']['latest'] = max(dates)
    
    return analysis

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 국민연금 관련 실제 데이터 수집 시작")
    print("=" * 60)
    
    all_data = []
    
    # 1. RSS 피드 수집
    print("\n[1/3] RSS 피드 수집 중...")
    rss_data = collect_rss_feeds()
    all_data.extend(rss_data)
    print(f"✅ RSS 수집 완료: {len(rss_data)}개")
    
    # 2. Reddit 데이터 수집
    print("\n[2/3] Reddit 데이터 수집 중...")
    reddit_data = collect_reddit_data()
    all_data.extend(reddit_data)
    print(f"✅ Reddit 수집 완료: {len(reddit_data)}개")
    
    # 3. 댓글 데이터 수집 (비활성화) - 실제 소스 API 연동 필요 시 별도 구현
    print("\n[3/3] 댓글 데이터 수집은 비활성화되어 있습니다 (REAL DATA ONLY 정책)")
    
    # 분석 결과
    print("\n" + "=" * 60)
    print("📊 수집 결과 분석")
    print("=" * 60)
    
    analysis = analyze_collected_data(all_data)
    
    print(f"\n총 수집 데이터: {analysis['total_count']}개")
    
    print("\n플랫폼별 분포:")
    for platform, count in analysis['by_platform'].items():
        print(f"  - {platform}: {count}개")
    
    print("\n카테고리별 분포:")
    for category, count in analysis['by_category'].items():
        print(f"  - {category}: {count}개")
    
    print("\n상위 작성자 (Top 10):")
    for i, author in enumerate(analysis['top_authors'], 1):
        print(f"  {i}. {author['name']}: {author['post_count']}개 (ID: {author['id']})")
    
    # 데이터 저장
    output_file = f"/home/nodove/workspace/Capstone/data/collected_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'total_count': len(all_data),
                'analysis': analysis
            },
            'data': all_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 데이터 저장 완료: {output_file}")
    
    # 샘플 출력
    print("\n" + "=" * 60)
    print("📝 샘플 데이터 (처음 5개)")
    print("=" * 60)
    
    for i, item in enumerate(all_data[:5], 1):
        print(f"\n[{i}] {item.get('title', item.get('content', ''))[:100]}...")
        print(f"   작성자: {item['author']} (ID: {item['author_id']})")
        print(f"   출처: {item['source']} | 플랫폼: {item['platform']}")
        print(f"   URL: {item.get('url', 'N/A')}")
    
    return all_data

if __name__ == "__main__":
    collected_data = main()
    print(f"\n✨ 완료! 총 {len(collected_data)}개의 데이터를 수집했습니다.")
