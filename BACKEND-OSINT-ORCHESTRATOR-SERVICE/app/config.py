import os
from typing import Optional

class Settings:
    def __init__(self):
        # 서버 설정
        self.port = int(os.getenv("PORT", 8005))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # 데이터베이스 설정 (환경 변수 필수, 기본값 없음)
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.secret_key = os.getenv("SECRET_KEY", "osint-orchestrator-secret-key")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Task orchestrator specific settings
        self.max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "10000"))
        self.task_timeout_default = int(os.getenv("TASK_TIMEOUT_DEFAULT", "3600"))  # 1 hour
        self.max_retries_default = int(os.getenv("MAX_RETRIES_DEFAULT", "3"))
        self.worker_heartbeat_timeout = int(os.getenv("WORKER_HEARTBEAT_TIMEOUT", "300"))  # 5 minutes
        self.priority_recalc_interval = int(os.getenv("PRIORITY_RECALC_INTERVAL", "60"))  # 1 minute
        
        # Queue management
        self.high_priority_threshold = float(os.getenv("HIGH_PRIORITY_THRESHOLD", "100"))
        self.critical_priority_threshold = float(os.getenv("CRITICAL_PRIORITY_THRESHOLD", "1000"))
        self.max_workers_per_task_type = int(os.getenv("MAX_WORKERS_PER_TASK_TYPE", "10"))
        
        # Event publishing (환경 변수 사용 권장)
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.nats_url = os.getenv("NATS_URL")
        self.event_publisher = os.getenv("EVENT_PUBLISHER", "kafka")  # kafka or nats
        
        # Alert routing
        self.alert_service_url = os.getenv("ALERT_SERVICE_URL", "http://alert-service:8004")
        self.system_alert_rule_id = os.getenv("SYSTEM_ALERT_RULE_ID")  # optional rule id for system-generated alerts
        
        # Service discovery (Compose 서비스 DNS 사용)
        self.planning_service_url = os.getenv("PLANNING_SERVICE_URL", "http://osint-planning:8006")
        self.source_service_url = os.getenv("SOURCE_SERVICE_URL", "http://osint-source:8007")
        self.collector_service_url = os.getenv("COLLECTOR_SERVICE_URL", "http://collector-service:8002")
        self.analysis_service_url = os.getenv("ANALYSIS_SERVICE_URL", "http://analysis-service:8001")

settings = Settings()