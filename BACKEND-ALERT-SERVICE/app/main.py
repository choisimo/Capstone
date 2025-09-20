"""
Alert Service 메인 모듈

연금 감성 분석 알림 서비스입니다.
이상 패턴 감지, 알림 규칙 관리, 사용자 통지 기능을 제공합니다.

주요 기능:
- 알림 생성 및 관리
- 알림 규칙 설정
- 이메일/SMS/웹 푸시 알림
- 알림 히스토리 관리
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.db import engine, Base
from app.routers import alerts, rules, notifications
from app.config import settings

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Pension Sentiment Alert Service",  # 서비스 제목
    description="Notification and alerting system for pension sentiment analysis",  # 서비스 설명
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
app.include_router(alerts.router, prefix="/alerts", tags=["Alert Management"])  # 알림 관리 라우터
app.include_router(rules.router, prefix="/rules", tags=["Alert Rules"])  # 알림 규칙 라우터
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])  # 알림 전송 라우터

@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 이벤트
    
    서비스 시작 시 데이터베이스 테이블을 생성합니다.
    """
    Base.metadata.create_all(bind=engine)  # SQLAlchemy 모델 기반 테이블 생성

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
        "service": "alert-service"  # 서비스 이름
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
        "service": "Pension Sentiment Alert Service",  # 서비스 이름
        "version": "1.0.0",  # 버전
        "status": "running",  # 실행 상태
        "endpoints": {  # 사용 가능한 엔드포인트 목록
            "alerts": "/alerts - 알림 관리",
            "rules": "/rules - 알림 규칙 설정",
            "notifications": "/notifications - 알림 처리",
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
        port=8004  # Alert 서비스 포트 (8004)
    )