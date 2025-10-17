import os
from typing import Optional

class Settings:
    def __init__(self):
        # 서버 설정
        self.port = int(os.getenv("PORT", 8007))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # 데이터베이스 설정 (환경 변수 우선, 기본값 없음)
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.secret_key = os.getenv("SECRET_KEY", "osint-source-secret-key")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Source registry specific settings
        self.max_sources_per_request = int(os.getenv("MAX_SOURCES_PER_REQUEST", "100"))
        self.robots_txt_cache_ttl = int(os.getenv("ROBOTS_TXT_CACHE_TTL", "86400"))  # 24 hours
        self.source_validation_timeout = int(os.getenv("SOURCE_VALIDATION_TIMEOUT", "30"))
        self.trust_score_threshold = float(os.getenv("TRUST_SCORE_THRESHOLD", "0.3"))
        
        # Event publishing (환경 변수 사용 권장)
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.nats_url = os.getenv("NATS_URL")
        self.event_publisher = os.getenv("EVENT_PUBLISHER", "kafka")  # kafka or nats
        
        # Source configuration
        self.sources_config_file = os.getenv("SOURCES_CONFIG_FILE", "data/sources.yaml")
        self.enable_dynamic_sources = os.getenv("ENABLE_DYNAMIC_SOURCES", "true").lower() == "true"
        self.default_user_agent = os.getenv("DEFAULT_USER_AGENT", "PensionSentiment-Bot/1.0")
        
        # Monitoring settings
        self.monitoring_interval = int(os.getenv("MONITORING_INTERVAL", "300"))  # 5 minutes
        self.max_consecutive_failures = int(os.getenv("MAX_CONSECUTIVE_FAILURES", "5"))
        self.http_timeout = int(os.getenv("HTTP_TIMEOUT", "10"))

settings = Settings()