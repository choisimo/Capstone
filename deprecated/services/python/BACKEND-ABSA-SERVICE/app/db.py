"""
ABSA Service 데이터베이스 모듈

속성 기반 감성 분석 서비스의 데이터베이스 연결 및 모델을 정의합니다.
"""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from app.config import settings
import uuid
from datetime import datetime

# SQLAlchemy 설정
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_size=10,  # 연결 풀 크기
    max_overflow=20  # 최대 오버플로우
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db():
    """
    데이터베이스 세션 생성 의존성
    
    FastAPI 엔드포인트에서 사용할 데이터베이스 세션을 생성하고 관리합니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ABSAAnalysis(Base):
    """
    ABSA 분석 결과 모델
    
    속성별 감성 분석 결과를 저장합니다.
    """
    __tablename__ = "absa_analyses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String, index=True)  # 컨텐츠 ID
    text = Column(Text)  # 분석 대상 텍스트
    
    # 속성별 분석 결과 (JSON 형태로 저장)
    aspects = Column(JSON)  # 추출된 속성 리스트
    aspect_sentiments = Column(JSON)  # 속성별 감성 점수
    
    # 전체 요약 정보
    overall_sentiment = Column(Float)  # 전체 감성 점수
    confidence_score = Column(Float)  # 신뢰도 점수
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AspectModel(Base):
    """
    속성 모델 정의
    
    분석에 사용할 속성 카테고리를 정의합니다.
    """
    __tablename__ = "aspect_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)  # 속성 이름
    description = Column(Text)  # 속성 설명
    keywords = Column(JSON)  # 관련 키워드 리스트
    
    # 모델 설정
    model_version = Column(String)  # 모델 버전
    is_active = Column(Integer, default=1)  # 활성화 상태
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
