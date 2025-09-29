"""
데이터베이스 모델 정의
페르소나, 사용자 연결, 콘텐츠 추적을 위한 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class UserPersona(Base):
    """사용자 페르소나 프로필"""
    __tablename__ = "user_personas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), index=True, nullable=False)
    platform = Column(String(50), index=True)
    
    # 프로필 데이터 (JSON)
    profile_data = Column(JSON, nullable=False)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_calculated_at = Column(DateTime, index=True)

    # 관계
    connections_as_user1 = relationship("UserConnection", foreign_keys="UserConnection.user1_id", back_populates="user1")
    connections_as_user2 = relationship("UserConnection", foreign_keys="UserConnection.user2_id", back_populates="user2")
    activities = relationship("UserActivity", back_populates="user")

    # 인덱스
    __table_args__ = (
        Index('idx_user_platform', 'username', 'platform'),
    )


class IdentityLinkRequest(Base):
    """신원 링크 요청"""
    __tablename__ = "identity_link_requests"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), index=True, nullable=False)
    identifier = Column(String(255), index=True, nullable=False)
    canonical_id = Column(String(64), index=True)  # 승인 시 채워짐 (선택)
    status = Column(String(20), index=True, default="pending")  # pending/approved/rejected

    evidence_type = Column(String(50))  # oauth/challenge/other
    evidence_ref = Column(String(1000))  # 증빙 URL/nonce hash 등

    requester_role = Column(String(50))
    requester_sub = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    decided_at = Column(DateTime)
    decided_by = Column(String(255))

    __table_args__ = (
        Index('idx_identity_link_req_unique_pending', 'platform', 'identifier', 'status'),
    )


class IdentityAuditLog(Base):
    """신원 링크/언링크 등 감사 로그"""
    __tablename__ = "identity_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String(50), index=True)
    actor_sub = Column(String(255), index=True)
    action = Column(String(50), index=True)  # link_request/approve/reject/link/unlink
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


 


class UserConnection(Base):
    """사용자 간 연결 관계"""
    __tablename__ = "user_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(String(255), ForeignKey("user_personas.user_id"), nullable=False)
    user2_id = Column(String(255), ForeignKey("user_personas.user_id"), nullable=False)
    
    # 연결 메트릭
    connection_strength = Column(Float, default=0.0, index=True)
    interaction_count = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    sentiment_history = Column(JSON)  # 감정 점수 히스토리
    
    # 공통 관심사
    common_topics = Column(JSON)  # {topic: count}
    
    # 타임스탬프
    first_interaction = Column(DateTime)
    last_interaction = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    user1 = relationship("UserPersona", foreign_keys=[user1_id], back_populates="connections_as_user1")
    user2 = relationship("UserPersona", foreign_keys=[user2_id], back_populates="connections_as_user2")
    
    # 인덱스
    __table_args__ = (
        Index('idx_connection_users', 'user1_id', 'user2_id', unique=True),
        Index('idx_connection_strength', 'connection_strength'),
    )


class Content(Base):
    """수집된 콘텐츠 (게시물)"""
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(255), unique=True, index=True)
    
    # 콘텐츠 정보
    title = Column(String(500))
    content = Column(Text, nullable=False)
    author = Column(String(255), index=True, nullable=False)
    url = Column(String(1000))
    source = Column(String(50), index=True)  # reddit, twitter, news_comment 등
    
    # 분석 결과
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))  # positive, negative, neutral
    topics = Column(JSON)  # 추출된 주제들
    aspects_analysis = Column(JSON)  # ABSA 분석 결과
    
    # 참여도 메트릭
    likes = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    
    # 메타데이터
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    comments = relationship("Comment", back_populates="parent_content")
    
    # 인덱스
    __table_args__ = (
        Index('idx_content_author_source', 'author', 'source'),
        Index('idx_content_sentiment', 'sentiment_score'),
        Index('idx_content_published', 'published_at'),
    )


class Comment(Base):
    """댓글"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(String(255), unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("contents.id"))
    
    # 댓글 정보
    content = Column(Text, nullable=False)
    author = Column(String(255), index=True, nullable=False)
    platform = Column(String(50))
    
    # 분석 결과
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    
    # 참여도
    likes = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # 메타데이터
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    parent_content = relationship("Content", back_populates="comments")
    
    # 인덱스
    __table_args__ = (
        Index('idx_comment_author', 'author'),
        Index('idx_comment_parent', 'parent_id'),
    )


class UserActivity(Base):
    """사용자 활동 추적"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("user_personas.user_id"), index=True)
    user_identifier = Column(String(255), index=True, nullable=False)
    platform = Column(String(50), index=True)
    
    # 활동 정보
    activity_type = Column(String(50))  # post, comment, reaction, share 등
    content_id = Column(String(255))
    content_type = Column(String(50))  # post, comment
    
    # 추적 정보
    tracked_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON)  # 추가 메타데이터
    
    # 관계
    user = relationship("UserPersona", back_populates="activities")
    
    # 인덱스
    __table_args__ = (
        Index('idx_activity_user_time', 'user_identifier', 'tracked_at'),
        Index('idx_activity_platform', 'platform', 'tracked_at'),
    )


class ABSAAnalysis(Base):
    """ABSA 분석 결과"""
    __tablename__ = "absa_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(255), unique=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"))
    
    # 분석 대상
    text = Column(Text, nullable=False)
    author = Column(String(255), index=True)
    
    # 전체 분석
    overall_sentiment = Column(String(20))
    overall_score = Column(Float)
    confidence = Column(Float)
    
    # 속성별 분석 (JSON)
    aspects_results = Column(JSON, nullable=False)
    # [
    #   {
    #     "aspect": "수익률",
    #     "sentiment": "positive",
    #     "score": 0.8,
    #     "confidence": 0.9,
    #     "keywords": ["수익", "이익"]
    #   }
    # ]
    
    # 모델 정보
    model_name = Column(String(100))
    model_version = Column(String(50))
    
    # 메타데이터
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_time_ms = Column(Integer)
    
    # 인덱스
    __table_args__ = (
        Index('idx_absa_author', 'author'),
        Index('idx_absa_sentiment', 'overall_sentiment', 'overall_score'),
    )


class Alert(Base):
    """알림"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), index=True)  # sentiment_surge, trending_topic, etc.
    severity = Column(String(20), index=True)  # low, medium, high, critical
    
    # 알림 내용
    title = Column(String(255), nullable=False)
    message = Column(Text)
    data = Column(JSON)  # 알림 관련 데이터
    
    # 상태
    status = Column(String(20), default="pending", index=True)  # pending, sent, acknowledged, resolved
    sent_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 인덱스
    __table_args__ = (
        Index('idx_alert_status_type', 'status', 'alert_type'),
        Index('idx_alert_created', 'created_at'),
    )


class TrendingTopic(Base):
    """트렌딩 주제"""
    __tablename__ = "trending_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), index=True, nullable=False)
    platform = Column(String(50), index=True)
    
    # 트렌드 메트릭
    mention_count = Column(Integer, default=0)
    unique_authors = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    sentiment_distribution = Column(JSON)  # {positive: %, negative: %, neutral: %}
    
    # 관련 키워드
    related_keywords = Column(JSON)  # [keyword1, keyword2, ...]
    sample_contents = Column(JSON)  # 샘플 콘텐츠 ID 리스트
    
    # 시간 범위
    time_window = Column(String(20))  # 1h, 24h, 7d 등
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime, index=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 인덱스
    __table_args__ = (
        Index('idx_trending_topic_time', 'topic', 'start_time', 'end_time'),
        Index('idx_trending_platform', 'platform', 'end_time'),
    )


class DataSource(Base):
    """데이터 소스 설정"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    source_type = Column(String(50))  # rss, api, web_scraping
    platform = Column(String(50))
    
    # 접속 정보
    url = Column(String(1000))
    api_key = Column(String(500))
    headers = Column(JSON)
    
    # 수집 설정
    is_active = Column(Boolean, default=True, index=True)
    crawl_interval_minutes = Column(Integer, default=60)
    max_items_per_crawl = Column(Integer, default=100)
    
    # 필터링
    keywords = Column(JSON)  # 수집할 키워드
    exclude_keywords = Column(JSON)  # 제외할 키워드
    
    # 상태
    last_crawled_at = Column(DateTime)
    last_error = Column(Text)
    total_items_collected = Column(Integer, default=0)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
