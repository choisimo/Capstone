"""ABSA service configuration backed by Consul KV."""

from __future__ import annotations

from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    PORT: int = Field(default=8003)
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Dependencies (required)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    ANALYSIS_SERVICE_URL: str = Field(default="http://analysis-service:8001")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="absa-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    # Request handling
    MAX_CONCURRENT_REQUESTS: int = Field(default=5)
    REQUEST_TIMEOUT: int = Field(default=30)

    # ABSA model tuning
    MODEL_CACHE_SIZE: int = Field(default=100)
    ASPECT_EXTRACTION_CONFIDENCE: float = Field(default=0.7)
    SENTIMENT_CONFIDENCE: float = Field(default=0.6)

    # Auth
    AUTH_JWT_SECRET: SecretStr | None = Field(default=None)
    AUTH_JWT_ALGORITHM: str = Field(default="HS256")
    AUTH_REQUIRED: bool = Field(default=False)

    # Persona freshness
    PERSONA_STALENESS_HOURS_DEFAULT: int = Field(default=24)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = [
        "DATABASE_URL",
        "REDIS_URL",
    ]
    return load_settings("absa-service", settings_cls=Settings, require=required)


settings = _load_settings()