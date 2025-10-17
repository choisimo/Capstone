"""
ABSA Service 설정 모듈

속성 기반 감성 분석 서비스의 설정을 관리합니다.
데이터베이스, 캐시, 모델 파라미터 등의 설정을 포함합니다.
"""

import os

class Settings:
    """
    서비스 설정 클래스
    
    환경 변수에서 설정을 읽어오며, 기본값을 제공합니다.
    """
    
    # 서버 설정
    port: int = int(os.getenv("PORT", 8003))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 데이터베이스 및 캐시 설정 (환경 변수 필수)
    database_url: str = os.getenv("DATABASE_URL")  # PostgreSQL URL
    redis_url: str = os.getenv("REDIS_URL")  # Redis 캐시 URL
    
    # 다른 서비스 연동 설정 (Compose 서비스 DNS)
    analysis_service_url: str = os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8001")  # 분석 서비스 URL
    
    # 요청 처리 설정
    max_concurrent_requests: int = 5  # 최대 동시 처리 요청 수
    request_timeout: int = 30  # 요청 타임아웃 (초)
    
    # ABSA 모델 설정
    model_cache_size: int = 100  # 모델 캐시 크기
    aspect_extraction_confidence: float = 0.7  # 속성 추출 신뢰도 임계값 (0.0~1.0)
    sentiment_confidence: float = 0.6  # 감성 분석 신뢰도 임계값 (0.0~1.0)

    # 인증 설정
    auth_jwt_secret: str = os.getenv("AUTH_JWT_SECRET", "")
    auth_jwt_algorithm: str = os.getenv("AUTH_JWT_ALG", "HS256")
    auth_required: bool = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

    # 페르소나 신선도 설정
    persona_staleness_hours_default: int = int(os.getenv("PERSONA_STALENESS_HOURS_DEFAULT", "24"))
    
    class Config:
        """
        설정 클래스 메타데이터
        """
        env_file = ".env"  # 환경 변수 파일 경로
        case_sensitive = False  # 대소문자 구분 안함

# 설정 싱글톤 인스턴스 생성
settings = Settings()