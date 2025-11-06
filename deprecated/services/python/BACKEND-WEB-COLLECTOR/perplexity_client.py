from __future__ import annotations
import json
import re
import requests
from typing import Any, Dict, List, Optional


class PerplexityClient:
    """
    Minimal Perplexity API client for fast web search via chat/completions.

    Notes:
    - Requires env var PPLX_API_KEY.
    - Uses chat/completions with an instruction to return a JSON object.
    - Includes a robust JSON extraction fallback to handle occasional formatting.
    """

    def __init__(self, base_url: str, api_key: str, model: str = "pplx-70b-online", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self.timeout = timeout

    def _extract_json(self, text: str) -> Dict[str, Any]:
        # Try direct parse first
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to find the first JSON object in the text
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise ValueError("Failed to parse JSON from Perplexity response")

    def search(self, q: str, top_k: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/chat/completions"
        system_prompt = (
            "You are a fast search results generator. "
            "Return strictly a compact JSON object with the key 'results' as an array of objects, "
            "each object containing keys: title (string), url (string), snippet (string), score (number between 0 and 1), source (string). "
            "Do not include any extra commentary."
        )
        user_prompt = (
            f"Query: {q}\n"
            f"Return top {top_k} results."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        content: Optional[str] = None
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            # In case the API format changes or error happens, raise a descriptive error
            raise RuntimeError(f"Unexpected Perplexity response format: {data}")
        parsed = self._extract_json(content)
        results = parsed.get("results") or []
        if not isinstance(results, list):
            raise RuntimeError("Perplexity response missing 'results' list")
        # Normalize fields and cap size
        out: List[Dict[str, Any]] = []
        for r in results[:top_k]:
            out.append({
                "title": str(r.get("title") or ""),
                "url": str(r.get("url") or ""),
                "snippet": str(r.get("snippet") or ""),
                "score": float(r.get("score") or 0.0),
                "source": str(r.get("source") or "perplexity"),
            })
        return out
