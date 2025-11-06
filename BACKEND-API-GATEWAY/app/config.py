"""API Gateway configuration module with Consul-backed loader."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    """Runtime configuration for the API Gateway service."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core service settings
    PORT: int = Field(default=8000, description="API Gateway server port")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Current runtime environment")

    # Service URLs (managed via Consul configs)
    ANALYSIS_SERVICE_URL: str = Field(..., description="URL for Analysis service")
    COLLECTOR_SERVICE_URL: str = Field(..., description="URL for Collector service")
    ABSA_SERVICE_URL: str = Field(..., description="URL for ABSA service")
    ALERT_SERVICE_URL: str = Field(..., description="URL for Alert service")
    OSINT_ORCHESTRATOR_SERVICE_URL: str = Field(..., description="URL for OSINT Orchestrator service")
    OSINT_PLANNING_SERVICE_URL: str = Field(..., description="URL for OSINT Planning service")
    OSINT_SOURCE_SERVICE_URL: str = Field(..., description="URL for OSINT Source service")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False, description="Enable Eureka service discovery")
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None, description="Comma-separated Eureka server URLs")
    EUREKA_APP_NAME: str = Field(default="api-gateway", description="Eureka application name for this gateway")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None, description="Override host reported to Eureka")
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None, description="Override IP reported to Eureka")
    EUREKA_METADATA: Optional[str] = Field(default=None, description="Extra metadata JSON for Eureka registration")

    # Timeouts
    DEFAULT_TIMEOUT: int = Field(default=30, description="Default outbound request timeout")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, description="Health check timeout")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Max requests per minute per IP")
    RATE_LIMIT_REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for rate limiting")

    # JWT configuration (secrets stored via Consul)
    JWT_SECRET_KEY: Optional[SecretStr] = Field(default=None, description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token lifespan")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    ALLOWED_METHODS: List[str] = Field(default_factory=lambda: ["*"])
    ALLOWED_HEADERS: List[str] = Field(default_factory=lambda: ["*"])

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    CONFIG_SYNC_TIMESTAMP: Optional[str] = Field(default=None, description="Last Consul sync timestamp")


def _load_settings() -> Settings:
    required_fields = [
        "ANALYSIS_SERVICE_URL",
        "COLLECTOR_SERVICE_URL",
        "ABSA_SERVICE_URL",
        "ALERT_SERVICE_URL",
        "OSINT_ORCHESTRATOR_SERVICE_URL",
        "OSINT_PLANNING_SERVICE_URL",
        "OSINT_SOURCE_SERVICE_URL",
    ]
    return load_settings("api-gateway", settings_cls=Settings, require=required_fields)


settings = _load_settings()