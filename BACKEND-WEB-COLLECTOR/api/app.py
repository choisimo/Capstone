"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import sys

# 경로 추가
sys.path.append('..')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 글로벌 시스템 인스턴스
from hybrid_crawler_main import HybridCrawlerSystem
_crawler_system = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    """
    global _crawler_system
    
    # 시작 시
    logger.info("Starting Hybrid Crawler API...")
    
    # 환경 변수 확인
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables")
    
    # 크롤러 시스템 초기화
    _crawler_system = HybridCrawlerSystem(gemini_api_key=gemini_api_key)
    await _crawler_system.start()
    logger.info("Crawler system started successfully")
    
    yield
    
    # 종료 시
    logger.info("Shutting down Hybrid Crawler API...")
    if _crawler_system:
        await _crawler_system.stop()
    logger.info("Shutdown complete")


# FastAPI 앱 생성
app = FastAPI(
    title="Hybrid Intelligent Crawling System API",
    description="AI-powered web crawling, monitoring, and analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 에러 핸들러"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else None
        }
    )


# 라우터 등록
from api.routes import (
    crawler_router,
    analysis_router,
    monitoring_router,
    workflow_router,
    system_router
)

app.include_router(crawler_router)
app.include_router(analysis_router)
app.include_router(monitoring_router)
app.include_router(workflow_router)
app.include_router(system_router)


# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트"""
    return {
        "name": "Hybrid Intelligent Crawling System",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "crawler": "/api/v1/crawler",
            "analysis": "/api/v1/analysis",
            "monitoring": "/api/v1/monitoring",
            "workflow": "/api/v1/workflow",
            "system": "/api/v1/system"
        }
    }


@app.get("/ping")
async def ping():
    """간단한 헬스 체크"""
    return {"ping": "pong"}


if __name__ == "__main__":
    import uvicorn
    
    # 개발 서버 실행
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
