from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, index=True, nullable=False)
    text = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False)  # daily, weekly, monthly
    entity = Column(String, nullable=False)  # pension fund, topic, etc.
    sentiment_trend = Column(Float, nullable=False)
    volume_trend = Column(Integer, nullable=False)
    keywords = Column(Text)  # JSON string
    confidence = Column(Float, nullable=False)
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # sentiment, trend, summary
    content = Column(Text, nullable=False)  # JSON string
    parameters = Column(Text)  # JSON string of generation parameters
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # sentiment, classification, etc.
    file_path = Column(String, nullable=False)
    metrics = Column(Text)  # JSON string
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())