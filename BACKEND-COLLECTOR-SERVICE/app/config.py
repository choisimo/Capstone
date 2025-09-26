import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 서버 설정
    port: int = int(os.getenv("PORT", 8002))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 데이터베이스 설정 (환경변수 직접 사용)
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

    # QA pipeline
    qa_enable_network_checks: bool = os.getenv("QA_ENABLE_NETWORK_CHECKS", "false").lower() == "true"
    qa_domain_whitelist: list = [
        "www.nps.or.kr",
        "nps.or.kr",
        "www.mohw.go.kr",
        "mohw.go.kr",
        "institute.nps.or.kr"
    ]
    qa_min_content_length: int = int(os.getenv("QA_MIN_CONTENT_LENGTH", "40"))
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()