import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Gateway Configuration
    PORT: int = 8000
    DEBUG: bool = True
    
    # Service URLs
    ANALYSIS_SERVICE_URL: str = "http://localhost:8001"
    COLLECTOR_SERVICE_URL: str = "http://localhost:8002"
    ABSA_SERVICE_URL: str = "http://localhost:8003"
    ALERT_SERVICE_URL: str = "http://localhost:8004"
    
    # Request Timeouts (seconds)
    DEFAULT_TIMEOUT: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Authentication (for future use)
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = ["*"]
    ALLOWED_METHODS: list = ["*"]
    ALLOWED_HEADERS: list = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()