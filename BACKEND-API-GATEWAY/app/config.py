"""
API Gateway 설정 모듈

환경 변수와 설정값을 관리하는 모듈입니다.
Pydantic을 사용하여 타입 체크와 검증을 수행합니다.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    API Gateway 설정 클래스
    
    환경 변수에서 설정을 읽어오며, .env 파일도 지원합니다.
    각 설정값은 환경 변수로 오버라이드할 수 있습니다.
    """
    
    # API Gateway 기본 설정
    PORT: int = 8000  # API Gateway 서버 포트
    DEBUG: bool = True  # 디버그 모드 (개발 환경에서 True, 프로덕션에서 False)
    
    # 마이크로서비스 URL 설정 (Compose 서비스 DNS 사용)
    ANALYSIS_SERVICE_URL: str = "http://analysis-service:8001"  # 분석 서비스 URL
    COLLECTOR_SERVICE_URL: str = "http://collector-service:8002"  # 수집 서비스 URL
    ABSA_SERVICE_URL: str = "http://absa-service:8003"  # ABSA 서비스 URL
    ALERT_SERVICE_URL: str = "http://alert-service:8004"  # 알림 서비스 URL
    OSINT_ORCHESTRATOR_SERVICE_URL: str = "http://osint-orchestrator:8005"  # OSINT 오케스트레이터 서비스 URL
    OSINT_PLANNING_SERVICE_URL: str = "http://osint-planning:8006"  # OSINT 계획 서비스 URL
    OSINT_SOURCE_SERVICE_URL: str = "http://osint-source:8007"  # OSINT 소스 서비스 URL
    
    # 요청 타임아웃 설정 (초 단위)
    DEFAULT_TIMEOUT: int = 30  # 일반 요청 타임아웃 (30초)
    HEALTH_CHECK_TIMEOUT: int = 5  # 헬스 체크 타임아웃 (5초)
    
    # Rate Limiting 설정 (분당 요청 수)
    RATE_LIMIT_PER_MINUTE: int = 100  # IP당 분당 최대 100개 요청 허용
    RATE_LIMIT_REDIS_URL: Optional[str] = None  # Redis URL (예: redis://redis:6379/0)
    
    # JWT 인증 설정 (향후 구현 예정)
    JWT_SECRET_KEY: Optional[str] = None  # JWT 시크릿 키 (필수 설정)
    JWT_ALGORITHM: str = "HS256"  # JWT 암호화 알고리즘
    JWT_EXPIRATION_HOURS: int = 24  # JWT 토큰 유효 시간 (24시간)
    
    # CORS(Cross-Origin Resource Sharing) 설정
    ALLOWED_ORIGINS: list = ["*"]  # 허용된 오리진 (프로덕션에서는 특정 도메인만 허용)
    ALLOWED_METHODS: list = ["*"]  # 허용된 HTTP 메서드
    ALLOWED_HEADERS: list = ["*"]  # 허용된 HTTP 헤더
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    # 환경 설정
    ENVIRONMENT: str = "development"  # 실행 환경 (development, staging, production)
    
    class Config:
        """
        Pydantic 설정 클래스
        
        환경 변수 읽기 옵션을 정의합니다.
        """
        env_file = ".env"  # .env 파일 경로
        case_sensitive = True  # 환경 변수명 대소문자 구분

# 설정 싱글톤 인스턴스 생성
# 애플리케이션 전체에서 이 인스턴스를 import하여 사용
settings = Settings()