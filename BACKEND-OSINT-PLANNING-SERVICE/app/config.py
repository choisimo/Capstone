import os

class Settings:
    # 서버 설정
    port: int = int(os.getenv("PORT", 8006))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 데이터베이스/브로커 설정 (환경 변수 필수, 기본값 없음)
    database_url: str = os.getenv("DATABASE_URL")
    redis_url: str = os.getenv("REDIS_URL")
    message_broker_url: str = os.getenv("MESSAGE_BROKER_URL")
    service_name: str = "osint-planning-service"
    log_level: str = "INFO"

settings = Settings()