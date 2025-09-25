"""
페르소나 분석 시스템
작성자의 댓글/게시글 히스토리를 추적하여 종합적인 페르소나 프로파일을 생성합니다.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import numpy as np
from dataclasses import dataclass, field
import json


@dataclass
class PersonaProfile:
    """페르소나 프로필 데이터 클래스"""
    user_id: str
    username: str
    total_posts: int = 0
    total_comments: int = 0
    
    # 감정 패턴
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    dominant_sentiment: str = "neutral"
    sentiment_volatility: float = 0.0  # 감정 변동성
    
    # 주요 관심사
    key_topics: List[str] = field(default_factory=list)
    topic_weights: Dict[str, float] = field(default_factory=dict)
    
    # 행동 패턴
    activity_patterns: Dict[str, Any] = field(default_factory=dict)
    posting_frequency: float = 0.0
    avg_post_length: float = 0.0
    
    # 언어 스타일
    vocabulary_richness: float = 0.0
    formality_level: float = 0.0
    argumentation_style: str = "neutral"  # aggressive, passive, assertive, neutral
    
    # 영향력 지표
    influence_score: float = 0.0
    engagement_rate: float = 0.0
    
    # 연관 사용자
    connected_users: List[str] = field(default_factory=list)
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # 추적 데이터
    tracked_sources: List[Dict[str, str]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "total_posts": self.total_posts,
            "total_comments": self.total_comments,
            "sentiment": {
                "distribution": self.sentiment_distribution,
                "dominant": self.dominant_sentiment,
                "volatility": self.sentiment_volatility
            },
            "topics": {
                "key_topics": self.key_topics,
                "weights": self.topic_weights
            },
            "behavior": {
                "activity_patterns": self.activity_patterns,
                "posting_frequency": self.posting_frequency,
                "avg_post_length": self.avg_post_length
            },
            "language": {
                "vocabulary_richness": self.vocabulary_richness,
                "formality_level": self.formality_level,
                "argumentation_style": self.argumentation_style
            },
            "influence": {
                "score": self.influence_score,
                "engagement_rate": self.engagement_rate
            },
            "connections": {
                "users": self.connected_users,
                "patterns": self.interaction_patterns
            },
            "metadata": {
                "tracked_sources": self.tracked_sources,
                "last_updated": self.last_updated.isoformat()
            }
        }


class PersonaAnalyzer:
    """페르소나 분석 및 추적 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.profiles_cache = {}
        
    async def analyze_user_persona(
        self, 
        user_identifier: str,
        platform: str,
        depth: int = 50  # 분석할 최대 게시물 수
    ) -> PersonaProfile:
        """
        사용자의 페르소나를 분석합니다.
        
        Args:
            user_identifier: 사용자 식별자 (ID, 닉네임 등)
            platform: 플랫폼 (reddit, twitter, news_comment 등)
            depth: 분석할 최대 게시물 수
            
        Returns:
            PersonaProfile: 분석된 페르소나 프로필
        """
        # 사용자 ID 생성
        user_id = self._generate_user_id(user_identifier, platform)
        
        # 캐시 확인
        if user_id in self.profiles_cache:
            cached_profile = self.profiles_cache[user_id]
            if self._is_cache_valid(cached_profile):
                return cached_profile
        
        # 사용자 콘텐츠 수집
        user_content = await self._fetch_user_content(user_identifier, platform, depth)
        
        if not user_content:
            # 새 프로필 생성
            return PersonaProfile(
                user_id=user_id,
                username=user_identifier,
                last_updated=datetime.utcnow()
            )
        
        # 페르소나 분석
        profile = await self._analyze_persona(user_id, user_identifier, user_content)
        
        # 캐시 저장
        self.profiles_cache[user_id] = profile
        
        # DB 저장
        await self._save_profile_to_db(profile)
        
        return profile
    
    async def _fetch_user_content(
        self, 
        user_identifier: str,
        platform: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        사용자의 콘텐츠를 데이터베이스에서 가져옵니다.
        """
        from app.models import Content, Comment
        
        contents = []
        
        # 게시물 조회
        posts = self.db.query(Content).filter(
            and_(
                Content.author == user_identifier,
                Content.source == platform
            )
        ).order_by(Content.created_at.desc()).limit(limit).all()
        
        for post in posts:
            contents.append({
                "type": "post",
                "id": post.id,
                "text": post.content,
                "title": post.title,
                "created_at": post.created_at,
                "url": post.url,
                "engagement": {
                    "likes": post.likes or 0,
                    "comments": post.comment_count or 0,
                    "shares": post.shares or 0
                },
                "sentiment": post.sentiment_score,
                "topics": post.topics or []
            })
        
        # 댓글 조회
        comments = self.db.query(Comment).filter(
            and_(
                Comment.author == user_identifier,
                Comment.platform == platform
            )
        ).order_by(Comment.created_at.desc()).limit(limit).all()
        
        for comment in comments:
            contents.append({
                "type": "comment",
                "id": comment.id,
                "text": comment.content,
                "created_at": comment.created_at,
                "parent_id": comment.parent_id,
                "engagement": {
                    "likes": comment.likes or 0,
                    "replies": comment.reply_count or 0
                },
                "sentiment": comment.sentiment_score
            })
        
        return contents
    
    async def _analyze_persona(
        self,
        user_id: str,
        username: str,
        contents: List[Dict[str, Any]]
    ) -> PersonaProfile:
        """
        수집된 콘텐츠를 기반으로 페르소나를 분석합니다.
        """
        profile = PersonaProfile(user_id=user_id, username=username)
        
        # 기본 통계
        posts = [c for c in contents if c["type"] == "post"]
        comments = [c for c in contents if c["type"] == "comment"]
        
        profile.total_posts = len(posts)
        profile.total_comments = len(comments)
        
        # 감정 분석
        sentiments = []
        for content in contents:
            if content.get("sentiment"):
                sentiments.append(content["sentiment"])
        
        if sentiments:
            profile.sentiment_distribution = self._calculate_sentiment_distribution(sentiments)
            profile.dominant_sentiment = max(profile.sentiment_distribution, 
                                            key=profile.sentiment_distribution.get)
            profile.sentiment_volatility = np.std(sentiments) if len(sentiments) > 1 else 0.0
        
        # 주제 분석
        all_topics = []
        for content in contents:
            if content.get("topics"):
                all_topics.extend(content["topics"])
        
        if all_topics:
            topic_counts = defaultdict(int)
            for topic in all_topics:
                topic_counts[topic] += 1
            
            # 상위 10개 주제
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            profile.key_topics = [t[0] for t in sorted_topics[:10]]
            
            total_mentions = sum(t[1] for t in sorted_topics)
            profile.topic_weights = {
                t[0]: t[1] / total_mentions 
                for t in sorted_topics[:10]
            }
        
        # 행동 패턴 분석
        if contents:
            # 게시 빈도 계산
            dates = [c["created_at"] for c in contents if c.get("created_at")]
            if len(dates) > 1:
                dates.sort()
                time_span = (dates[-1] - dates[0]).days + 1
                profile.posting_frequency = len(contents) / time_span if time_span > 0 else 0
            
            # 평균 글 길이
            lengths = [len(c.get("text", "")) for c in contents if c.get("text")]
            profile.avg_post_length = np.mean(lengths) if lengths else 0
            
            # 활동 패턴 (시간대별)
            hours = [c["created_at"].hour for c in contents if c.get("created_at")]
            if hours:
                hour_counts = defaultdict(int)
                for h in hours:
                    hour_counts[h] += 1
                profile.activity_patterns["hourly"] = dict(hour_counts)
        
        # 언어 스타일 분석
        all_text = " ".join([c.get("text", "") for c in contents if c.get("text")])
        if all_text:
            profile.vocabulary_richness = self._calculate_vocabulary_richness(all_text)
            profile.formality_level = self._calculate_formality_level(all_text)
            profile.argumentation_style = self._detect_argumentation_style(all_text)
        
        # 영향력 지표
        total_engagement = sum(
            sum(c.get("engagement", {}).values()) 
            for c in contents 
            if c.get("engagement")
        )
        profile.engagement_rate = total_engagement / len(contents) if contents else 0
        profile.influence_score = self._calculate_influence_score(profile)
        
        # 추적 소스 기록
        profile.tracked_sources = [
            {
                "type": c["type"],
                "id": str(c["id"]),
                "url": c.get("url", ""),
                "created_at": c["created_at"].isoformat() if c.get("created_at") else ""
            }
            for c in contents[:10]  # 최근 10개만 저장
        ]
        
        profile.last_updated = datetime.utcnow()
        
        return profile
    
    def _calculate_sentiment_distribution(self, sentiments: List[float]) -> Dict[str, float]:
        """감정 분포를 계산합니다."""
        positive = len([s for s in sentiments if s > 0.3])
        negative = len([s for s in sentiments if s < -0.3])
        neutral = len([s for s in sentiments if -0.3 <= s <= 0.3])
        
        total = len(sentiments)
        if total == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        
        return {
            "positive": positive / total,
            "negative": negative / total,
            "neutral": neutral / total
        }
    
    def _calculate_vocabulary_richness(self, text: str) -> float:
        """어휘 풍부도를 계산합니다."""
        words = re.findall(r'\b[a-z가-힣]+\b', text.lower())
        if not words:
            return 0.0
        
        unique_words = set(words)
        return len(unique_words) / len(words)
    
    def _calculate_formality_level(self, text: str) -> float:
        """문체의 격식 수준을 계산합니다."""
        # 간단한 휴리스틱: 존댓말, 격식체 표현 등
        formal_markers = [
            r'습니다', r'습니까', r'하십시오', r'드립니다',
            r'therefore', r'moreover', r'furthermore', r'however'
        ]
        
        informal_markers = [
            r'ㅋㅋ', r'ㅎㅎ', r'ㅠㅠ', r'야', r'네요',
            r'lol', r'omg', r'wtf', r'btw'
        ]
        
        formal_count = sum(1 for marker in formal_markers if re.search(marker, text, re.I))
        informal_count = sum(1 for marker in informal_markers if re.search(marker, text, re.I))
        
        if formal_count + informal_count == 0:
            return 0.5
        
        return formal_count / (formal_count + informal_count)
    
    def _detect_argumentation_style(self, text: str) -> str:
        """논증 스타일을 감지합니다."""
        aggressive_markers = ['절대', '무조건', '당연히', '틀렸', '말도 안']
        assertive_markers = ['생각합니다', '믿습니다', '확신합니다', '분명히']
        passive_markers = ['아마도', '혹시', '어쩌면', '그럴 수도', '모르겠']
        
        aggressive_count = sum(1 for marker in aggressive_markers if marker in text)
        assertive_count = sum(1 for marker in assertive_markers if marker in text)
        passive_count = sum(1 for marker in passive_markers if marker in text)
        
        counts = {
            'aggressive': aggressive_count,
            'assertive': assertive_count,
            'passive': passive_count
        }
        
        if max(counts.values()) == 0:
            return 'neutral'
        
        return max(counts, key=counts.get)
    
    def _calculate_influence_score(self, profile: PersonaProfile) -> float:
        """영향력 점수를 계산합니다."""
        # 가중치
        weights = {
            'engagement': 0.4,
            'frequency': 0.2,
            'consistency': 0.2,
            'topic_focus': 0.2
        }
        
        # 정규화된 점수들
        engagement_score = min(profile.engagement_rate / 100, 1.0)  # 100을 기준으로 정규화
        frequency_score = min(profile.posting_frequency / 10, 1.0)  # 하루 10개 기준
        consistency_score = 1.0 - profile.sentiment_volatility  # 일관성
        
        # 주제 집중도 (엔트로피 기반)
        if profile.topic_weights:
            entropy = -sum(w * np.log(w + 1e-10) for w in profile.topic_weights.values())
            max_entropy = np.log(len(profile.topic_weights))
            topic_focus_score = 1.0 - (entropy / max_entropy if max_entropy > 0 else 0)
        else:
            topic_focus_score = 0.0
        
        # 가중 평균
        influence = (
            weights['engagement'] * engagement_score +
            weights['frequency'] * frequency_score +
            weights['consistency'] * consistency_score +
            weights['topic_focus'] * topic_focus_score
        )
        
        return round(influence, 3)
    
    def _generate_user_id(self, identifier: str, platform: str) -> str:
        """고유한 사용자 ID를 생성합니다."""
        return hashlib.md5(f"{platform}:{identifier}".encode()).hexdigest()
    
    def _is_cache_valid(self, profile: PersonaProfile, max_age_hours: int = 24) -> bool:
        """캐시가 유효한지 확인합니다."""
        age = datetime.utcnow() - profile.last_updated
        return age < timedelta(hours=max_age_hours)
    
    async def _save_profile_to_db(self, profile: PersonaProfile):
        """프로필을 데이터베이스에 저장합니다."""
        from app.models import UserPersona
        
        # 기존 프로필 조회
        existing = self.db.query(UserPersona).filter(
            UserPersona.user_id == profile.user_id
        ).first()
        
        profile_data = json.dumps(profile.to_dict())
        
        if existing:
            # 업데이트
            existing.profile_data = profile_data
            existing.updated_at = datetime.utcnow()
        else:
            # 새로 생성
            new_persona = UserPersona(
                user_id=profile.user_id,
                username=profile.username,
                profile_data=profile_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(new_persona)
        
        self.db.commit()
    
    async def track_user_connections(
        self,
        user_id: str,
        interaction_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        사용자 간 연결 관계를 추적합니다.
        
        Args:
            user_id: 대상 사용자 ID
            interaction_data: 상호작용 데이터
            
        Returns:
            연결 관계 분석 결과
        """
        connections = defaultdict(lambda: {"count": 0, "sentiment": [], "topics": []})
        
        for interaction in interaction_data:
            other_user = interaction.get("other_user")
            if other_user:
                connections[other_user]["count"] += 1
                
                if interaction.get("sentiment"):
                    connections[other_user]["sentiment"].append(interaction["sentiment"])
                
                if interaction.get("topics"):
                    connections[other_user]["topics"].extend(interaction["topics"])
        
        # 연결 강도 계산
        for user, data in connections.items():
            # 평균 감정
            if data["sentiment"]:
                data["avg_sentiment"] = np.mean(data["sentiment"])
            
            # 공통 주제
            if data["topics"]:
                topic_counts = defaultdict(int)
                for topic in data["topics"]:
                    topic_counts[topic] += 1
                data["common_topics"] = list(dict(sorted(
                    topic_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]).keys())
            
            # 연결 강도 점수
            data["connection_strength"] = min(data["count"] / 10, 1.0)
        
        return dict(connections)
