"""Lightweight Consul client utility shared across services.

This module provides a small wrapper around Consul's HTTP KV API so that
microservices can consistently retrieve configuration without introducing
heavy external dependencies. It intentionally keeps the surface area minimal
and focuses on read-only access which aligns with the current requirement of
loading settings at service bootstrap time.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)


class ConsulClientError(RuntimeError):
    """Raised when Consul returns an unexpected response."""


class ConsulClient:
    """Simple HTTP client for Consul KV operations."""

    def __init__(
        self,
        base_url: str,
        *,
        token: Optional[str] = None,
        verify: bool = True,
        timeout: float = 5.0,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        if not base_url:
            raise ValueError("Consul base_url must be provided")

        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = f"http://{base_url}"

        default_headers: dict[str, str] = {}
        if token:
            default_headers["X-Consul-Token"] = token
        if headers:
            default_headers.update(headers)

        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=default_headers,
            timeout=timeout,
            verify=verify,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ConsulClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def list_keys(self, prefix: str) -> List[str]:
        """Return all keys under the provided prefix."""
        response = self._client.get(f"/v1/kv/{prefix}", params={"keys": "true"})
        if response.status_code == 404:
            return []
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ConsulClientError(str(exc)) from exc
        return response.json()

    def get_kv(self, key: str, *, recurse: bool = False) -> list[dict]:
        """Fetch KV pairs for the given key.

        When ``recurse`` is True, all nested keys will be returned. The
        response format matches Consul's REST API which returns a list of
        dictionaries containing base64 encoded values.
        """
        params = {"recurse": "true"} if recurse else None
        response = self._client.get(f"/v1/kv/{key}", params=params)
        if response.status_code == 404:
            return []
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ConsulClientError(str(exc)) from exc
        data = response.json()
        if not isinstance(data, list):
            raise ConsulClientError("Unexpected Consul response payload")
        return data


def boolean_from_env(name: str, default: bool = True) -> bool:
    """Parse boolean-like environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def build_default_client(**overrides) -> ConsulClient:
    """Factory that reads standard environment variables for configuration."""
    base_url = overrides.get("base_url") or os.getenv("CONSUL_HTTP_ADDR", "http://localhost:8500")
    token = overrides.get("token") or os.getenv("CONSUL_HTTP_TOKEN")
    verify = overrides.get("verify") if "verify" in overrides else boolean_from_env("CONSUL_HTTP_SSL_VERIFY", True)
    timeout = overrides.get("timeout") or float(os.getenv("CONSUL_HTTP_TIMEOUT", "5"))

    return ConsulClient(base_url, token=token, verify=verify, timeout=timeout)
