"""OSINT Planning Service configuration backed by Consul KV."""

from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    PORT: int = Field(default=8006)
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    SERVICE_NAME: str = Field(default="osint-planning-service")

    # Dependencies (required)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    MESSAGE_BROKER_URL: str = Field(...)

    # Planner specifics
    DEFAULT_PRIORITY: int = Field(default=5)
    MAX_KEYWORDS_PER_PLAN: int = Field(default=50)
    MAX_ACTIVE_PLANS: int = Field(default=20)

    # Integration endpoints
    ORCHESTRATOR_SERVICE_URL: str = Field(default="http://osint-orchestrator:8005")
    SOURCE_SERVICE_URL: str = Field(default="http://osint-source:8007")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="osint-planning-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = ["DATABASE_URL", "REDIS_URL", "MESSAGE_BROKER_URL"]
    return load_settings("osint-planning", settings_cls=Settings, require=required)


settings = _load_settings()