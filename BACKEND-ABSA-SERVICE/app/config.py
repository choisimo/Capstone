import os

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pension_sentiment")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    analysis_service_url: str = os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8001")
    
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    
    model_cache_size: int = 100
    aspect_extraction_confidence: float = 0.7
    sentiment_confidence: float = 0.6
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()