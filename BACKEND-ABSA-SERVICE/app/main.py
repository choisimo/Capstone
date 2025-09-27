"""
ABSA Service 메인 모듈

속성 기반 감성 분석(Aspect-Based Sentiment Analysis) 서비스입니다.
연금 관련 컨텐츠의 세부 속성별 감성을 분석합니다.

주요 기능:
- 속성 추출 (수익률, 안정성, 관리비용 등)
- 속성별 감성 분석
- ABSA 모델 관리
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.db import engine, Base
from app.routers import aspects, analysis, models
from app.config import settings

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Pension Sentiment ABSA Service",  # 서비스 제목
    description="Aspect-Based Sentiment Analysis for pension content",  # 서비스 설명
    version="1.0.0"  # API 버전
)

# CORS 미들웨어 추가 - 크로스 오리진 요청 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (프로덕션에서는 특정 도메인 지정 권장)
    allow_credentials=True,  # 쿠키/인증 정보 포함 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 라우터 등록 - 각 기능별 엔드포인트 그룹
app.include_router(aspects.router, prefix="/aspects", tags=["Aspect Extraction"])  # 속성 추출 관련 라우터
app.include_router(analysis.router, prefix="/analysis", tags=["ABSA Analysis"])  # ABSA 분석 관련 라우터
app.include_router(models.router, prefix="/models", tags=["ABSA Models"])  # ABSA 모델 관리 라우터

# 페르소나 분석 라우터 추가
try:
    from app.routers import personas
    app.include_router(personas.router, prefix="/api/v1", tags=["Persona Analysis"])  # 페르소나 분석 라우터
except ImportError:
    pass  # 페르소나 모듈이 없는 경우 무시

@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 이벤트
    
    서비스 시작 시 데이터베이스 테이블을 생성합니다.
    """
    Base.metadata.create_all(bind=engine)  # SQLAlchemy 모델 기반 테이블 생성
    # Also create tables from app.models Base (separate declarative base)
    try:
        from app import models as models_module
        models_module.Base.metadata.create_all(bind=engine)
    except Exception:
        # Non-fatal; some environments may not have models module available or tables already exist
        pass
    # Best-effort runtime migration for new columns
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE user_personas ADD COLUMN IF NOT EXISTS last_calculated_at TIMESTAMP"))
            conn.commit()
    except Exception:
        # Ignore if DB does not support IF NOT EXISTS or lacks permissions
        pass

@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    
    서비스의 상태를 확인하기 위한 엔드포인트입니다.
    API Gateway에서 주기적으로 호출합니다.
    
    Returns:
        dict: 서비스 상태 정보
    """
    return {
        "status": "healthy",  # 서비스 상태
        "service": "absa-service"  # 서비스 이름
    }

@app.get("/")
async def root():
    """
    루트 엔드포인트
    
    서비스의 기본 정보와 사용 가능한 엔드포인트 목록을 제공합니다.
    
    Returns:
        dict: 서비스 정보 및 엔드포인트 목록
    """
    return {
        "service": "Pension Sentiment ABSA Service",  # 서비스 이름
        "version": "1.0.0",  # 버전
        "status": "running",  # 실행 상태
        "endpoints": {  # 사용 가능한 엔드포인트 목록
            "aspects": "/aspects - 속성 추출 작업",
            "analysis": "/analysis - ABSA 분석 작업",
            "models": "/models - ABSA 모델 관리",
            "health": "/health - 헬스 체크",
            "docs": "/docs - API 문서"
        }
    }

if __name__ == "__main__":
    """
    직접 실행 시 진입점
    
    개발 환경에서 python main.py로 직접 실행할 때 사용됩니다.
    """
    uvicorn.run(
        app,  # FastAPI 애플리케이션 인스턴스
        host="0.0.0.0",  # 모든 네트워크 인터페이스에서 접속 허용
        port=8003  # ABSA 서비스 포트 (8003)
    )