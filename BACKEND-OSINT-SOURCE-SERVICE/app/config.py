import os
from typing import Optional

class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/osint_db")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.secret_key = os.getenv("SECRET_KEY", "osint-source-secret-key")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Source registry specific settings
        self.max_sources_per_request = int(os.getenv("MAX_SOURCES_PER_REQUEST", "100"))
        self.robots_txt_cache_ttl = int(os.getenv("ROBOTS_TXT_CACHE_TTL", "86400"))  # 24 hours
        self.source_validation_timeout = int(os.getenv("SOURCE_VALIDATION_TIMEOUT", "30"))
        self.trust_score_threshold = float(os.getenv("TRUST_SCORE_THRESHOLD", "0.3"))
        
        # Event publishing
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.event_publisher = os.getenv("EVENT_PUBLISHER", "kafka")  # kafka or nats

settings = Settings()