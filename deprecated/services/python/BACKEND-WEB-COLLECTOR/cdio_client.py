from __future__ import annotations
import requests
from typing import Dict, Any, Optional


class ChangeDetectionClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    # ---- Watches ----
    def list_watches(self, tag: Optional[str] = None) -> Dict[str, Any]:
        params = {"tag": tag} if tag else None
        resp = self.session.get(f"{self.base_url}/watch", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def create_watch(self, payload: Dict[str, Any]) -> str:
        resp = self.session.post(
            f"{self.base_url}/watch", json=payload, timeout=60,
            headers={**self.session.headers, "Content-Type": "application/json"}
        )
        resp.raise_for_status()
        # create returns text/plain "OK"
        return resp.text

    def get_watch(self, uuid: str, recheck: Optional[bool] = None,
                  paused: Optional[str] = None, muted: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if recheck:
            params["recheck"] = "true"
        if paused in ("paused", "unpaused"):
            params["paused"] = paused
        if muted in ("muted", "unmuted"):
            params["muted"] = muted
        resp = self.session.get(f"{self.base_url}/watch/{uuid}", params=params, timeout=60)
        resp.raise_for_status()
        # Could be JSON (full watch) or text/plain "OK"
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype:
            return resp.json()
        return resp.text

    def update_watch(self, uuid: str, watch_json: Dict[str, Any]) -> str:
        resp = self.session.put(
            f"{self.base_url}/watch/{uuid}", json=watch_json, timeout=60,
            headers={**self.session.headers, "Content-Type": "application/json"}
        )
        resp.raise_for_status()
        return resp.text

    def delete_watch(self, uuid: str) -> str:
        resp = self.session.delete(f"{self.base_url}/watch/{uuid}", timeout=30)
        resp.raise_for_status()
        return resp.text

    # ---- Search ----
    def search(self, q: str, partial: bool = False, tag: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"q": q}
        if partial:
            params["partial"] = "true"
        if tag:
            params["tag"] = tag
        resp = self.session.get(f"{self.base_url}/search", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---- Tags ----
    def list_tags(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/tags", timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---- Import ----
    def import_urls(self, text: str, tag: Optional[str] = None, tag_uuids: Optional[str] = None,
                    proxy: Optional[str] = None, dedupe: Optional[bool] = True) -> Any:
        params: Dict[str, Any] = {}
        if tag:
            params["tag"] = tag
        if tag_uuids:
            params["tag_uuids"] = tag_uuids
        if proxy:
            params["proxy"] = proxy
        if dedupe is not None:
            params["dedupe"] = str(dedupe).lower()
        headers = {**self.session.headers, "Content-Type": "text/plain"}
        resp = self.session.post(f"{self.base_url}/import", params=params, data=text, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    # ---- System ----
    def systeminfo(self) -> Dict[str, Any]:
        resp = self.session.get(f"{self.base_url}/systeminfo", timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ---- History/Snapshots ----
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
