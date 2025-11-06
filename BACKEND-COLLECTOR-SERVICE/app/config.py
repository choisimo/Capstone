"""Collector service configuration leveraging Consul-backed loader."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    # Core runtime configuration
    PORT: int = Field(default=8002, description="Collector service port")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Dependencies
    DATABASE_URL: str = Field(..., description="Primary database connection URL")
    REDIS_URL: str = Field(..., description="Redis connection URL")
    ANALYSIS_SERVICE_URL: str = Field(..., description="Analysis service base URL")

    # Processing parameters
    MAX_CONCURRENT_REQUESTS: int = Field(default=10)
    REQUEST_TIMEOUT: int = Field(default=30, description="HTTP request timeout (seconds)")
    COLLECTION_INTERVAL: int = Field(default=3600, description="Collection interval in seconds")
    USER_AGENT: str = Field(default="PensionSentimentCollector/1.0")

    RSS_FEEDS: List[str] = Field(default_factory=list)
    SCRAPING_TARGETS: List[str] = Field(default_factory=list)

    # QA pipeline
    QA_ENABLE_NETWORK_CHECKS: bool = Field(default=False)
    QA_DOMAIN_WHITELIST: List[str] = Field(default_factory=list)
    QA_EXPECTED_KEYWORDS: Optional[List[str]] = Field(default=None)
    QA_MIN_CONTENT_LENGTH: int = Field(default=40)

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="collector-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None, description="JSON metadata for Eureka registration")

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = ["DATABASE_URL", "REDIS_URL", "ANALYSIS_SERVICE_URL"]
    return load_settings("collector-service", settings_cls=Settings, require=required)


settings = _load_settings()