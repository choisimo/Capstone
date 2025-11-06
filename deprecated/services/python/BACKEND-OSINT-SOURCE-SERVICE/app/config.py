"""OSINT Source Service configuration backed by Consul KV."""

from __future__ import annotations

from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    PORT: int = Field(default=8007)
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # Dependencies (required)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    SECRET_KEY: SecretStr = Field(...)

    # Source registry specifics
    MAX_SOURCES_PER_REQUEST: int = Field(default=100)
    ROBOTS_TXT_CACHE_TTL: int = Field(default=86400)
    SOURCE_VALIDATION_TIMEOUT: int = Field(default=30)
    TRUST_SCORE_THRESHOLD: float = Field(default=0.3)

    # Event publishing
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = Field(default=None)
    NATS_URL: Optional[str] = Field(default=None)
    EVENT_PUBLISHER: str = Field(default="kafka")

    # Source configuration
    SOURCES_CONFIG_FILE: str = Field(default="data/sources.yaml")
    ENABLE_DYNAMIC_SOURCES: bool = Field(default=True)
    DEFAULT_USER_AGENT: str = Field(default="PensionSentiment-Bot/1.0")

    # Monitoring settings
    MONITORING_INTERVAL: int = Field(default=300)
    MAX_CONSECUTIVE_FAILURES: int = Field(default=5)
    HTTP_TIMEOUT: int = Field(default=10)

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="osint-source-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]
    return load_settings("osint-source", settings_cls=Settings, require=required)


settings = _load_settings()