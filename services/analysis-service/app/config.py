import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/pension_sentiment"
    REDIS_URL: str = "redis://localhost:6379"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    API_GATEWAY_URL: str = "http://localhost:8000"
    COLLECTOR_SERVICE_URL: str = "http://localhost:8002"
    ABSA_SERVICE_URL: str = "http://localhost:8003"
    ALERT_SERVICE_URL: str = "http://localhost:8004"
    
    ML_MODEL_PATH: str = "/app/models"
    CACHE_TTL: int = 300
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()