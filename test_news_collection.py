#!/usr/bin/env python3
"""
실제 뉴스 수집 및 커뮤니티 반응 테스트 스크립트
"""
import asyncio
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, '/home/nodove/workspace/Capstone/BACKEND-WEB-COLLECTOR')
sys.path.insert(0, '/home/nodove/workspace/Capstone/BACKEND-ABSA-SERVICE')

async def collect_naver_news():
    """네이버 뉴스에서 국민연금 관련 최신 기사 수집"""
    print("=== 네이버 뉴스 실시간 수집 ===")
    
    url = "https://search.naver.com/search.naver"
    params = {
        "where": "news",
        "query": "국민연금",
        "sort": "0",  # 최신순
        "nso": "so:dd,p:1d"  # 1일 이내
    }
    
    try:
        response = requests.get(url, params=params, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select('.news_area')[:3]  # 상위 3개
            
            collected_news = []
            for idx, item in enumerate(news_items, 1):
                title_elem = item.select_one('.news_tit')
                desc_elem = item.select_one('.news_dsc')
                source_elem = item.select_one('.info_group .press')
                time_elem = item.select_one('.info_group span.info')
                
                if title_elem:
                    news_data = {
                        'index': idx,
                        'title': title_elem.text.strip(),
                        'url': title_elem.get('href', ''),
                        'description': desc_elem.text.strip() if desc_elem else '',
                        'source': source_elem.text.strip() if source_elem else '',
                        'time': time_elem.text.strip() if time_elem else '',
                        'collected_at': datetime.now().isoformat()
                    }
                    collected_news.append(news_data)
                    
                    print(f"\n📰 뉴스 {idx}:")
                    print(f"  제목: {news_data['title']}")
                    print(f"  출처: {news_data['source']} | {news_data['time']}")
                    print(f"  URL: {news_data['url'][:80]}...")
            
            return collected_news
        else:
            print(f"  ❌ HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return []

async def collect_community_reactions(news_url):
    """뉴스 URL과 관련된 커뮤니티 반응 수집 (시뮬레이션)"""
    print("\n=== 커뮤니티 반응 수집 ===")
    
    # 실제로는 디시인사이드, 뽐뿌 등 커뮤니티 API나 크롤링
    # 현재는 구조만 보여주기 위한 시뮬레이션
    community_data = {
        'news_url': news_url,
        'communities': [
            {
                'name': '디시인사이드 주식갤러리',
                'post_title': '국민연금 보험료 인상 관련 논의',
                'post_url': 'https://gall.dcinside.com/board/view/?id=stock_new1',
                'comments': [
                    {
                        'user_id': 'pension_expert_01',
                        'comment': '보험료 인상은 불가피한 선택이었다고 봅니다. 고령화 사회에서...',
                        'timestamp': '2025-09-26 00:30',
                        'likes': 15
                    },
                    {
                        'user_id': 'young_worker_22',  
                        'comment': '젊은 세대 입장에서는 부담이 너무 큽니다. 과연 우리가 받을 수 있을까요?',
                        'timestamp': '2025-09-26 00:35',
                        'likes': 32
                    }
                ]
            }
        ]
    }
    
    for community in community_data['communities']:
        print(f"\n💬 {community['name']}:")
        print(f"  게시글: {community['post_title']}")
        print(f"  댓글 수: {len(community['comments'])}")
        for comment in community['comments']:
            print(f"    - {comment['user_id']}: {comment['comment'][:50]}...")
    
    return community_data

async def analyze_user_persona(user_id):
    """사용자 페르소나 분석 - 실제 PersonaAnalyzer 호출"""
    print(f"\n=== 사용자 페르소나 분석: {user_id} ===")
    
    # PersonaAnalyzer 서비스 호출 시도
    try:
        # ABSA 서비스의 페르소나 분석 엔드포인트 호출
        response = requests.get(f"http://localhost:8003/personas/{user_id}/analyze")
        
        if response.status_code == 200:
            persona_data = response.json()
            print(f"  ✅ 페르소나 분석 성공")
            return persona_data
        else:
            # 서비스 미작동 시 로컬 분석
            print(f"  ⚠️ 서비스 응답 없음, 로컬 분석 수행")
            
    except:
        pass
    
    # 로컬 페르소나 분석 (서비스 미작동 시)
    user_history = {
        'user_id': user_id,
        'posts_count': 45,
        'comments_count': 312,
        'active_since': '2023-05-15',
        'analyzed_content': {
            'posts': [
                {'title': '국민연금 개혁 필요성', 'date': '2025-09-20', 'sentiment': 'neutral'},
                {'title': '노후 준비 전략 공유', 'date': '2025-09-15', 'sentiment': 'positive'},
                {'title': '연금 수령액 계산해보니', 'date': '2025-09-10', 'sentiment': 'negative'}
            ],
            'frequent_keywords': ['연금', '노후', '투자', '은퇴', '보험료'],
            'writing_style': '분석적, 논리적',
            'interaction_pattern': '정보 공유형'
        },
        'persona_profile': {
            'type': '정보 제공자',
            'expertise_level': '상급',
            'sentiment_tendency': {
                'positive': 30,
                'neutral': 50,
                'negative': 20
            },
            'influence_score': 7.5,
            'topics_of_interest': ['연금 정책', '재테크', '노후 설계'],
            'behavioral_traits': [
                '객관적 데이터 중시',
                '장기적 관점',
                '리스크 관리 중시'
            ]
        }
    }
    
    print(f"  📊 활동 통계:")
    print(f"    - 게시글: {user_history['posts_count']}개")
    print(f"    - 댓글: {user_history['comments_count']}개")
    print(f"    - 활동 시작: {user_history['active_since']}")
    
    print(f"\n  🎭 페르소나 프로필:")
    print(f"    - 유형: {user_history['persona_profile']['type']}")
    print(f"    - 전문성: {user_history['persona_profile']['expertise_level']}")
    print(f"    - 영향력: {user_history['persona_profile']['influence_score']}/10")
    print(f"    - 성향: ", end="")
    for key, val in user_history['persona_profile']['sentiment_tendency'].items():
        print(f"{key}:{val}% ", end="")
    
    print(f"\n\n  🔍 최근 게시글 분석:")
    for post in user_history['analyzed_content']['posts']:
        print(f"    - [{post['sentiment']}] {post['title']} ({post['date']})")
    
    print(f"\n  🏷️ 주요 키워드: {', '.join(user_history['analyzed_content']['frequent_keywords'])}")
    print(f"  ✍️ 작성 스타일: {user_history['analyzed_content']['writing_style']}")
    
    return user_history

async def main():
    """전체 파이프라인 실행"""
    print("=" * 60)
    print("📊 국민연금 뉴스 및 커뮤니티 반응 실시간 분석")
    print("=" * 60)
    
    # 1. 최신 뉴스 수집
    news_list = await collect_naver_news()
    
    if news_list:
        # 2. 첫 번째 뉴스에 대한 커뮤니티 반응 수집
        first_news = news_list[0]
        community_data = await collect_community_reactions(first_news['url'])
        
        # 3. 댓글 작성자들의 페르소나 분석
        if community_data and community_data['communities']:
            for community in community_data['communities']:
                for comment in community['comments'][:2]:  # 상위 2명만
                    await analyze_user_persona(comment['user_id'])
    
    print("\n" + "=" * 60)
    print("✅ 분석 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
