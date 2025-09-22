import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pension_sentiment")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    analysis_service_url: str = os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8001")
    
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    collection_interval: int = 3600  # 1 hour
    
    user_agent: str = "PensionSentimentCollector/1.0"
    
    rss_feeds: list = [
        "https://feeds.feedburner.com/pensionsweek",
        "https://www.pensions-pmi.org.uk/feed/",
        "https://www.pensionsage.com/pa/RSS-news.xml"
    ]
    
    scraping_targets: list = [
        "https://www.thepensionsregulator.gov.uk/en/media-hub/press-releases",
        "https://www.pensionsage.com/news/",
        "https://www.professionaladviser.com/pensions/"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()