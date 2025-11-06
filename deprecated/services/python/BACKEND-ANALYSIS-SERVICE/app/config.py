"""Analysis Service configuration backed by Consul KV."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    """Runtime configuration for the analysis service."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    PORT: int = Field(default=8001)

    # Dependencies (required)
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # Service URLs
    API_GATEWAY_URL: str = Field(...)
    COLLECTOR_SERVICE_URL: str = Field(...)
    ABSA_SERVICE_URL: str = Field(...)
    ALERT_SERVICE_URL: str = Field(...)

    # Security
    SECRET_KEY: SecretStr = Field(..., description="JWT/crypto secret")
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["*"])

    # ML & caching
    ML_MODEL_PATH: str = Field(default="/app/models")
    CACHE_TTL: int = Field(default=300)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="analysis-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = [
        "DATABASE_URL",
        "REDIS_URL",
        "API_GATEWAY_URL",
        "COLLECTOR_SERVICE_URL",
        "ABSA_SERVICE_URL",
        "ALERT_SERVICE_URL",
        "SECRET_KEY",
    ]
    return load_settings("analysis-service", settings_cls=Settings, require=required)


settings = _load_settings()