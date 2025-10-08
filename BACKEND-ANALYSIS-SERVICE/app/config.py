"""
Analysis Service 설정 모듈

환경 변수 및 서비스 설정을 관리하는 모듈입니다.
.env 파일에서 설정을 읽어오며, 환경 변수로 오버라이드 가능합니다.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    서비스 설정 클래스
    
    환경 변수에서 설정을 읽어오고 타입 검증을 수행합니다.
    기본값은 개발 환경을 위한 설정이며, 프로덕션에서는 환경 변수로 오버라이드합니다.
    """
    
    # 데이터베이스 설정 (환경 변수 사용 권장, 기본값 제거)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")  # PostgreSQL 연결 URL
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")  # Redis 캐시 서버 URL
    
    # 애플리케이션 설정
    DEBUG: bool = True  # 디버그 모드 (개발: True, 프로덕션: False)
    SECRET_KEY: str = "your-secret-key-here"  # JWT 및 암호화용 비밀 키
    ALLOWED_HOSTS: List[str] = ["*"]  # CORS 허용 호스트 목록
    
    # 마이크로서비스 URL 설정 (Compose 서비스 DNS 사용)
    API_GATEWAY_URL: str = "http://api-gateway:8000"  # API Gateway URL
    COLLECTOR_SERVICE_URL: str = "http://collector-service:8002"  # 수집 서비스 URL
    ABSA_SERVICE_URL: str = "http://absa-service:8003"  # ABSA 서비스 URL
    ALERT_SERVICE_URL: str = "http://alert-service:8004"  # 알림 서비스 URL
    
    # ML 모델 및 캐싱 설정
    ML_MODEL_PATH: str = "/app/models"  # ML 모델 저장 경로
    CACHE_TTL: int = 300  # 캐시 유효 시간 (300초 = 5분)
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    class Config:
        """
        Pydantic 설정 클래스
        
        환경 변수 로드 옵션을 설정합니다.
        """
        env_file = ".env"  # .env 파일에서 환경 변수 로드


# 설정 싱글톤 인스턴스 생성
# 애플리케이션 전체에서 이 인스턴스를 import하여 사용
settings = Settings()