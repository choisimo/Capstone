"""Lightweight Eureka client wrapper for Python services.

Centralises py_eureka_client usage so microservices can opt-in without
copy/pasting boilerplate. The dependency is optional; when the library is not
available or integration is disabled, the helpers become no-ops.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from py_eureka_client import eureka_client  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    eureka_client = None  # type: ignore


def _normalise_urls(urls: Optional[Sequence[str] | str]) -> list[str]:
    if urls is None:
        return []
    if isinstance(urls, str):
        urls = [segment.strip() for segment in urls.split(",")]
    return [url for url in (u.strip() for u in urls) if url]


def _parse_metadata(value: Optional[str | Dict[str, Any]]) -> Dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        logger.warning("Failed to decode Eureka metadata JSON; ignoring value")
    return {}


@dataclass(slots=True)
class EurekaConfig:
    enabled: bool
    service_urls: Sequence[str] = field(default_factory=list)
    app_name: str = ""
    instance_port: int = 0
    instance_host: Optional[str] = None
    instance_ip: Optional[str] = None
    prefer_ip_address: bool = True
    secure_port_enabled: bool = False
    secure_port: Optional[int] = None
    heartbeat_interval: Optional[int] = None
    renewal_retry_interval: Optional[int] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_settings(
        cls,
        *,
        enabled: bool,
        service_urls: Sequence[str] | str | None,
        app_name: str,
        instance_port: int,
        instance_host: Optional[str] = None,
        instance_ip: Optional[str] = None,
        prefer_ip_address: bool = True,
        secure_port_enabled: bool = False,
        secure_port: Optional[int] = None,
        heartbeat_interval: Optional[int] = None,
        renewal_retry_interval: Optional[int] = None,
        metadata: Optional[str | Dict[str, Any]] = None,
    ) -> "EurekaConfig":
        urls = _normalise_urls(service_urls)
        metadata_map = _parse_metadata(metadata)
        return cls(
            enabled=enabled and bool(urls),
            service_urls=urls,
            app_name=app_name,
            instance_port=instance_port,
            instance_host=instance_host,
            instance_ip=instance_ip,
            prefer_ip_address=prefer_ip_address,
            secure_port_enabled=secure_port_enabled,
            secure_port=secure_port,
            heartbeat_interval=heartbeat_interval,
            renewal_retry_interval=renewal_retry_interval,
            metadata=metadata_map,
        )


class _BaseEurekaManager:
    async def register(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def deregister(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @property
    def is_enabled(self) -> bool:
        return False


class NullEurekaManager(_BaseEurekaManager):
    async def register(self) -> None:
        return None

    async def deregister(self) -> None:
        return None


class EurekaManager(_BaseEurekaManager):
    def __init__(self, config: EurekaConfig) -> None:
        self._config = config
        self._client: Any = None
        self._lock = asyncio.Lock()

    @property
    def is_enabled(self) -> bool:
        return self._config.enabled

    async def register(self) -> None:
        if not self._config.enabled:
            return
        if eureka_client is None:
            logger.warning(
                "py-eureka-client is not installed; skipping Eureka registration"
            )
            return
        async with self._lock:
            if self._client is not None:
                return
            eureka_server = ",".join(self._config.service_urls)
            kwargs: Dict[str, Any] = {
                "eureka_server": eureka_server,
                "app_name": self._config.app_name,
                "instance_port": self._config.instance_port,
                "prefer_ip_address": self._config.prefer_ip_address,
            }
            optional_fields = {
                "instance_host": self._config.instance_host,
                "instance_ip": self._config.instance_ip,
                "secure_port": self._config.secure_port,
                "secure_port_enabled": self._config.secure_port_enabled,
                "heartbeat_interval": self._config.heartbeat_interval,
                "renewal_interval_in_sec": self._config.renewal_retry_interval,
            }
            for key, value in optional_fields.items():
                if value is not None:
                    kwargs[key] = value
            if self._config.metadata:
                kwargs["metadata"] = self._config.metadata

            try:
                client = eureka_client.EurekaClient(**kwargs)  # type: ignore[arg-type]
                await client.start()
                self._client = client
                logger.info(
                    "Registered service '%s' on port %s with Eureka",
                    self._config.app_name,
                    self._config.instance_port,
                )
            except Exception as exc:  # pragma: no cover - network dependent
                logger.error("Failed to register with Eureka: %s", exc, exc_info=True)
                self._client = None

    async def deregister(self) -> None:
        if not self._config.enabled or self._client is None:
            return
        async with self._lock:
            client, self._client = self._client, None
        try:
            await client.stop()
            logger.info("Deregistered service '%s' from Eureka", self._config.app_name)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Failed to deregister from Eureka cleanly: %s", exc)


def create_eureka_manager(config: Optional[EurekaConfig]) -> _BaseEurekaManager:
    if config is None or not config.enabled:
        return NullEurekaManager()
    return EurekaManager(config)


def create_manager_from_settings(
    *,
    enabled: bool,
    service_urls: Sequence[str] | str | None,
    app_name: str,
    instance_port: int,
    instance_host: Optional[str] = None,
    instance_ip: Optional[str] = None,
    prefer_ip_address: bool = True,
    secure_port_enabled: bool = False,
    secure_port: Optional[int] = None,
    heartbeat_interval: Optional[int] = None,
    renewal_retry_interval: Optional[int] = None,
    metadata: Optional[str | Dict[str, Any]] = None,
) -> _BaseEurekaManager:
    config = EurekaConfig.from_settings(
        enabled=enabled,
        service_urls=service_urls,
        app_name=app_name,
        instance_port=instance_port,
        instance_host=instance_host,
        instance_ip=instance_ip,
        prefer_ip_address=prefer_ip_address,
        secure_port_enabled=secure_port_enabled,
        secure_port=secure_port,
        heartbeat_interval=heartbeat_interval,
        renewal_retry_interval=renewal_retry_interval,
        metadata=metadata,
    )
    if not config.enabled:
        logger.debug("Eureka disabled or missing service URLs – manager is no-op")
    return create_eureka_manager(config)


__all__ = [
    "EurekaConfig",
    "EurekaManager",
    "NullEurekaManager",
    "create_eureka_manager",
    "create_manager_from_settings",
]
