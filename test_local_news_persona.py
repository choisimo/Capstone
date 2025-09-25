#!/usr/bin/env python3
"""
로컬 환경에서 실제 데이터 구조를 시뮬레이션하여 페르소나 분석 테스트
"""
import json
from datetime import datetime, timedelta
import random

class LocalNewsCollector:
    """로컬 뉴스 수집 시뮬레이터"""
    
    def collect_real_news(self):
        """실제 뉴스 데이터 구조 시뮬레이션"""
        # 이것은 실제 네이버 뉴스 API 응답 구조를 모방
        news_data = [
            {
                "title": "국민연금 보험료율 인상 논의 본격화…노사정 협의 시작",
                "originallink": "https://www.hani.co.kr/arti/economy/economy_general/1234567.html",
                "link": "https://n.news.naver.com/mnews/article/028/0002654321",
                "description": "정부가 국민연금 보험료율 인상을 위한 노사정 협의를 본격 시작했다. 현재 9%인 보험료율을 단계적으로 13%까지 인상하는 방안이 유력하게 검토되고 있다.",
                "pubDate": "2025-09-26 09:15:00",
                "source": "한겨레"
            },
            {
                "title": "[속보] 국민연금 기금운용수익률 7.2% 기록",
                "originallink": "https://www.mk.co.kr/news/economy/10876543",
                "link": "https://n.news.naver.com/mnews/article/009/0005234567",
                "description": "국민연금기금운용본부는 올해 상반기 기금운용수익률이 7.2%를 기록했다고 밝혔다. 해외주식 투자 비중 확대가 주효했다는 분석이다.",
                "pubDate": "2025-09-26 08:30:00",
                "source": "매일경제"
            },
            {
                "title": "젊은층 '국민연금 불신' 확산…'내가 받을 수 있을까' 우려",
                "originallink": "https://www.chosun.com/economy/economy_general/2025/09/26/ABC123",
                "link": "https://n.news.naver.com/mnews/article/023/0003789012",
                "description": "20-30대 젊은층 사이에서 국민연금에 대한 불신이 확산되고 있다. 설문조사 결과 응답자의 73%가 '노후에 연금을 받을 수 없을 것'이라고 답했다.",
                "pubDate": "2025-09-26 07:45:00",
                "source": "조선일보"
            }
        ]
        return news_data

class LocalCommunityCollector:
    """로컬 커뮤니티 반응 수집 시뮬레이터"""
    
    def collect_community_reactions(self, news_title):
        """실제 커뮤니티 댓글 구조 시뮬레이션"""
        reactions = {
            "news_title": news_title,
            "communities": [
                {
                    "platform": "dcinside",
                    "board": "stock_gallery",
                    "post": {
                        "title": f"[펌] {news_title}",
                        "author": "연금전문가123",
                        "created_at": "2025-09-26 10:30:00",
                        "views": 1523,
                        "comments_count": 87
                    },
                    "top_comments": [
                        {
                            "id": "c_001",
                            "author_id": "pension_master",
                            "author_nickname": "연금마스터",
                            "content": "보험료 인상은 불가피합니다. 현재 9%로는 지속가능성이 없어요. OECD 평균이 18.7%인 걸 생각하면 우리나라는 아직도 낮은 편입니다.",
                            "created_at": "2025-09-26 10:35:00",
                            "likes": 45,
                            "dislikes": 12,
                            "replies_count": 8
                        },
                        {
                            "id": "c_002",
                            "author_id": "young_worker_88",
                            "author_nickname": "청년노동자",
                            "content": "월급도 안오르는데 보험료만 올린다고? 지금도 힘든데 13%까지 올리면 실수령액이 얼마나 줄어들지... 차라리 개인연금에 투자하는게 낫지 않나요?",
                            "created_at": "2025-09-26 10:40:00",
                            "likes": 89,
                            "dislikes": 5,
                            "replies_count": 15
                        }
                    ]
                },
                {
                    "platform": "ppomppu",
                    "board": "freeboard",
                    "post": {
                        "title": "국민연금 보험료 인상 관련 의견",
                        "author": "ppom1234",
                        "created_at": "2025-09-26 11:00:00",
                        "views": 892,
                        "comments_count": 43
                    },
                    "top_comments": [
                        {
                            "id": "p_001",
                            "author_id": "finance_pro",
                            "author_nickname": "재테크프로",
                            "content": "국민연금보다 개인연금, IRP 늘리는게 답입니다. 정부 믿지 마세요.",
                            "created_at": "2025-09-26 11:05:00",
                            "likes": 67,
                            "dislikes": 8,
                            "replies_count": 12
                        }
                    ]
                }
            ]
        }
        return reactions

class PersonaAnalyzer:
    """사용자 페르소나 분석기"""
    
    def analyze_user_history(self, user_id):
        """사용자의 과거 활동 이력 분석"""
        
        # 실제 DB에서 가져올 데이터 구조 시뮬레이션
        user_history = {
            "user_id": user_id,
            "platform": "dcinside",
            "registration_date": "2021-03-15",
            "stats": {
                "total_posts": 234,
                "total_comments": 1876,
                "total_likes_received": 3421,
                "total_dislikes_received": 456
            },
            "recent_posts": [
                {
                    "title": "국민연금 개혁안 정리해봄",
                    "content": "최근 발표된 국민연금 개혁안을 정리해봤습니다...",
                    "created_at": "2025-09-25 14:30:00",
                    "views": 523,
                    "comments": 34,
                    "sentiment": "neutral",
                    "keywords": ["국민연금", "개혁", "보험료", "수령액"]
                },
                {
                    "title": "노후준비 어떻게 하시나요?",
                    "content": "30대 직장인입니다. 국민연금만으로는 불안해서...",
                    "created_at": "2025-09-20 09:15:00",
                    "views": 892,
                    "comments": 67,
                    "sentiment": "negative",
                    "keywords": ["노후준비", "불안", "개인연금", "투자"]
                }
            ],
            "recent_comments": [
                {
                    "content": "보험료 인상은 어쩔 수 없는 선택이라고 봅니다.",
                    "created_at": "2025-09-26 10:35:00",
                    "sentiment": "neutral",
                    "parent_post": "보험료 인상 논의",
                    "likes": 45
                },
                {
                    "content": "젊은 세대 입장도 고려해야 합니다.",
                    "created_at": "2025-09-25 16:20:00",
                    "sentiment": "negative",
                    "parent_post": "연금개혁 필요성",
                    "likes": 23
                }
            ],
            "writing_patterns": {
                "avg_length": 125.5,  # 평균 글자 수
                "vocabulary_diversity": 0.72,  # 어휘 다양성
                "formality": 0.65,  # 격식체 사용 비율
                "emoticon_usage": 0.05,  # 이모티콘 사용 비율
                "question_ratio": 0.15  # 질문형 문장 비율
            }
        }
        
        # 페르소나 프로필 생성
        persona_profile = self._generate_persona_profile(user_history)
        return user_history, persona_profile
    
    def _generate_persona_profile(self, history):
        """히스토리 기반 페르소나 프로필 생성"""
        
        # 감성 분석
        sentiments = []
        for post in history.get("recent_posts", []):
            sentiments.append(post.get("sentiment", "neutral"))
        for comment in history.get("recent_comments", []):
            sentiments.append(comment.get("sentiment", "neutral"))
        
        sentiment_counts = {}
        for s in sentiments:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        total = len(sentiments) if sentiments else 1
        sentiment_distribution = {k: v/total*100 for k, v in sentiment_counts.items()}
        
        # 키워드 추출
        all_keywords = []
        for post in history.get("recent_posts", []):
            all_keywords.extend(post.get("keywords", []))
        
        keyword_freq = {}
        for k in all_keywords:
            keyword_freq[k] = keyword_freq.get(k, 0) + 1
        
        # 페르소나 타입 결정
        stats = history.get("stats", {})
        patterns = history.get("writing_patterns", {})
        
        persona_type = "분석가형"  # 기본값
        if stats.get("total_posts", 0) > 200:
            persona_type = "정보 제공자형"
        elif patterns.get("question_ratio", 0) > 0.3:
            persona_type = "질문자형"
        elif patterns.get("emoticon_usage", 0) > 0.2:
            persona_type = "친근한 조언자형"
        
        # 영향력 점수 계산 (0-10)
        influence_score = min(10, (
            stats.get("total_likes_received", 0) / 500 +
            stats.get("total_posts", 0) / 50 +
            stats.get("total_comments", 0) / 200
        ))
        
        profile = {
            "persona_type": persona_type,
            "expertise_level": "중상급" if stats.get("total_posts", 0) > 100 else "초중급",
            "sentiment_distribution": sentiment_distribution,
            "dominant_sentiment": max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral",
            "key_interests": list(keyword_freq.keys())[:5],
            "influence_score": round(influence_score, 1),
            "behavioral_traits": [],
            "writing_style": "",
            "engagement_pattern": ""
        }
        
        # 행동 특성 분석
        if patterns.get("formality", 0) > 0.6:
            profile["behavioral_traits"].append("격식적")
            profile["writing_style"] = "논리적이고 체계적"
        else:
            profile["behavioral_traits"].append("친근함")
            profile["writing_style"] = "편안하고 대화체적"
        
        if patterns.get("avg_length", 0) > 150:
            profile["behavioral_traits"].append("상세한 설명")
        else:
            profile["behavioral_traits"].append("간결한 표현")
        
        # 참여 패턴
        if stats.get("total_comments", 0) > stats.get("total_posts", 0) * 5:
            profile["engagement_pattern"] = "적극적 토론 참여형"
        else:
            profile["engagement_pattern"] = "정보 공유 중심형"
        
        return profile

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🔍 실제 뉴스 수집 및 사용자 페르소나 분석 시스템 테스트")
    print("=" * 70)
    
    # 1. 뉴스 수집
    print("\n[STEP 1] 📰 최신 뉴스 수집")
    print("-" * 60)
    news_collector = LocalNewsCollector()
    news_list = news_collector.collect_real_news()
    
    for idx, news in enumerate(news_list, 1):
        print(f"\n뉴스 {idx}:")
        print(f"  제목: {news['title']}")
        print(f"  출처: {news['source']} | {news['pubDate']}")
        print(f"  링크: {news['link']}")
        print(f"  요약: {news['description'][:60]}...")
    
    # 2. 커뮤니티 반응 수집
    print("\n\n[STEP 2] 💬 커뮤니티 반응 수집")
    print("-" * 60)
    community_collector = LocalCommunityCollector()
    reactions = community_collector.collect_community_reactions(news_list[0]['title'])
    
    for community in reactions['communities']:
        print(f"\n플랫폼: {community['platform']} - {community['board']}")
        print(f"  게시글: {community['post']['title']}")
        print(f"  작성자: {community['post']['author']}")
        print(f"  조회수: {community['post']['views']:,} | 댓글: {community['post']['comments_count']}")
        
        print("\n  주요 댓글:")
        for comment in community['top_comments']:
            print(f"    [{comment['author_nickname']}] ({comment['likes']}👍/{comment['dislikes']}👎)")
            print(f"    {comment['content'][:80]}...")
    
    # 3. 사용자 페르소나 분석
    print("\n\n[STEP 3] 👤 사용자 페르소나 상세 분석")
    print("-" * 60)
    persona_analyzer = PersonaAnalyzer()
    
    # 첫 번째 댓글 작성자 분석
    test_users = ["pension_master", "young_worker_88"]
    
    for user_id in test_users:
        print(f"\n>>> 사용자 분석: {user_id}")
        print("=" * 50)
        
        history, profile = persona_analyzer.analyze_user_history(user_id)
        
        print(f"\n📊 활동 통계:")
        print(f"  가입일: {history['registration_date']}")
        print(f"  총 게시글: {history['stats']['total_posts']:,}개")
        print(f"  총 댓글: {history['stats']['total_comments']:,}개")
        print(f"  받은 좋아요: {history['stats']['total_likes_received']:,}개")
        
        print(f"\n🎭 페르소나 프로필:")
        print(f"  유형: {profile['persona_type']}")
        print(f"  전문성: {profile['expertise_level']}")
        print(f"  영향력: {profile['influence_score']}/10")
        
        print(f"\n💭 감정 성향:")
        for sentiment, percentage in profile['sentiment_distribution'].items():
            bar = "■" * int(percentage/5)
            print(f"  {sentiment:8s}: {bar:20s} {percentage:.1f}%")
        print(f"  주요 감정: {profile['dominant_sentiment']}")
        
        print(f"\n📝 작성 패턴:")
        print(f"  스타일: {profile['writing_style']}")
        print(f"  참여 유형: {profile['engagement_pattern']}")
        print(f"  특징: {', '.join(profile['behavioral_traits'])}")
        
        print(f"\n🔑 관심 키워드:")
        print(f"  {', '.join(profile['key_interests'])}")
        
        print(f"\n📜 최근 활동:")
        for post in history['recent_posts'][:2]:
            print(f"  [{post['created_at'][:10]}] {post['title']}")
            print(f"    조회 {post['views']:,} | 댓글 {post['comments']} | 감정: {post['sentiment']}")
    
    print("\n" + "=" * 70)
    print("✅ 분석 완료 - 실제 데이터 구조 기반 시뮬레이션")
    print("=" * 70)

if __name__ == "__main__":
    main()
