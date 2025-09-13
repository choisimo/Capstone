from __future__ import annotations
import requests
from typing import Dict, Any, Optional


class ChangeDetectionClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    def list_watches(self, tag: Optional[str] = None) -> Dict[str, Any]:
        params = {"tag": tag} if tag else None
        resp = self.session.get(f"{self.base_url}/watch", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_watch_history(self, uuid: str) -> Dict[str, str]:
        resp = self.session.get(f"{self.base_url}/watch/{uuid}/history", timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_snapshot(self, uuid: str, timestamp: str = "latest", html: bool = False) -> str:
        params = {"html": "1"} if html else None
        resp = self.session.get(
            f"{self.base_url}/watch/{uuid}/history/{timestamp}", params=params, timeout=60
        )
        resp.raise_for_status()
        return resp.text
