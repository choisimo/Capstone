"""OSINT Orchestrator configuration backed by Consul KV."""

from __future__ import annotations

from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    PORT: int = Field(default=8005)
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # Dependencies (required)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    SECRET_KEY: SecretStr = Field(...)

    # Task orchestrator specifics
    MAX_QUEUE_SIZE: int = Field(default=10000)
    TASK_TIMEOUT_DEFAULT: int = Field(default=3600)
    MAX_RETRIES_DEFAULT: int = Field(default=3)
    WORKER_HEARTBEAT_TIMEOUT: int = Field(default=300)
    PRIORITY_RECALC_INTERVAL: int = Field(default=60)

    HIGH_PRIORITY_THRESHOLD: float = Field(default=100.0)
    CRITICAL_PRIORITY_THRESHOLD: float = Field(default=1000.0)
    MAX_WORKERS_PER_TASK_TYPE: int = Field(default=10)

    # Event publishing
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = Field(default=None)
    NATS_URL: Optional[str] = Field(default=None)
    EVENT_PUBLISHER: str = Field(default="kafka")

    # Alert routing
    ALERT_SERVICE_URL: str = Field(default="http://alert-service:8004")
    SYSTEM_ALERT_RULE_ID: Optional[int] = Field(default=None)

    # Service discovery
    PLANNING_SERVICE_URL: str = Field(default="http://osint-planning:8006")
    SOURCE_SERVICE_URL: str = Field(default="http://osint-source:8007")
    COLLECTOR_SERVICE_URL: str = Field(default="http://collector-service:8002")
    ANALYSIS_SERVICE_URL: str = Field(default="http://analysis-service:8001")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="osint-orchestrator")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]
    return load_settings("osint-orchestrator", settings_cls=Settings, require=required)


settings = _load_settings()