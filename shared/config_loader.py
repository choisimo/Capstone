"""Consul-backed configuration loading utilities."""
from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from typing import Any, Dict, Iterable, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings

from .consul_client import ConsulClient, ConsulClientError, build_default_client

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound=BaseSettings)

_CACHE: dict[tuple[str, str], tuple[float, Dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
_DEFAULT_TTL_SECONDS = float(os.getenv("CONSUL_CACHE_TTL", "60"))


def _normalize_key(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in raw)
    return cleaned.upper()


def _decode_value(value_b64: Optional[str]) -> Optional[str]:
    if value_b64 in (None, ""):
        return None
    try:
        decoded = base64.b64decode(value_b64, validate=True).decode("utf-8")
    except Exception as exc:
        raise ConsulClientError(f"Invalid base64 payload: {exc}") from exc
    return decoded.strip()


def _parse_value(raw: Optional[str]) -> Any:
    if raw is None:
        return None
    lower = raw.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "none"}:
        return None
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        try:
            return int(raw)
        except ValueError:
            pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.startswith("{") or raw.startswith("["):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Failed to decode JSON value: %s", raw)
    return raw


class ConfigLoader:
    """Fetch and cache configuration for a given service/environment."""

    def __init__(
        self,
        service: str,
        *,
        env: Optional[str] = None,
        client: Optional[ConsulClient] = None,
        cache_ttl: float = _DEFAULT_TTL_SECONDS,
    ) -> None:
        self.service = service
        self.environment = env or os.getenv("ENVIRONMENT", "development")
        self.client = client or build_default_client()
        self.cache_ttl = cache_ttl

    @property
    def _config_prefix(self) -> str:
        return f"config/{self.service}/{self.environment}/configs"

    @property
    def _secret_prefix(self) -> str:
        return f"secrets/{self.service}/{self.environment}"

    def _load_prefix(self, prefix: str) -> Dict[str, Any]:
        items: Dict[str, Any] = {}
        response = self.client.get_kv(prefix, recurse=True)
        for entry in response:
            key = entry.get("Key")
            raw_value = entry.get("Value")
            if not key:
                continue
            if not key.startswith(prefix):
                continue
            suffix = key[len(prefix) :].lstrip("/")
            if not suffix:
                continue
            normalized = _normalize_key(suffix)
            decoded = _decode_value(raw_value)
            parsed = _parse_value(decoded)
            items[normalized] = parsed
        return items

    def fetch(self) -> Dict[str, Any]:
        cache_key = (self.service, self.environment)
        with _CACHE_LOCK:
            cached = _CACHE.get(cache_key)
            if cached and (time.time() - cached[0]) < self.cache_ttl:
                return dict(cached[1])
        data: Dict[str, Any] = {}
        try:
            data.update(self._load_prefix(self._config_prefix))
        except ConsulClientError as exc:
            logger.warning("Failed to load config prefix %s: %s", self._config_prefix, exc)
        try:
            data.update(self._load_prefix(self._secret_prefix))
        except ConsulClientError as exc:
            logger.warning("Failed to load secret prefix %s: %s", self._secret_prefix, exc)
        with _CACHE_LOCK:
            _CACHE[cache_key] = (time.time(), dict(data))
        return data


def load_settings(
    service: str,
    *,
    settings_cls: Type[_T],
    env: Optional[str] = None,
    require: Optional[Iterable[str]] = None,
    cache_ttl: float = _DEFAULT_TTL_SECONDS,
) -> _T:
    """Load settings for the given service using Consul-backed loader.

    Args:
        service: Logical service name used for Consul prefixes.
        settings_cls: Pydantic BaseSettings subclass to instantiate.
        env: Optional override for ENVIRONMENT.
        require: Iterable of field names expected to be populated.
        cache_ttl: Seconds to retain cached values in-memory.

    Returns:
        Instance of ``settings_cls`` populated from Consul and environment overrides.
    """

    loader = ConfigLoader(service, env=env, cache_ttl=cache_ttl)
    consul_data = loader.fetch()

    overrides = {key: os.getenv(key, value) for key, value in consul_data.items() if value is not None}

    try:
        instance = settings_cls(**overrides)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration for {service}: {exc}") from exc

    missing: list[str] = []
    if require:
        for field in require:
            value = getattr(instance, field, None)
            if value in (None, ""):
                missing.append(field)
    if missing:
        raise ValueError(
            f"Missing required configuration values for {service}: {', '.join(missing)}"
        )

    return instance
