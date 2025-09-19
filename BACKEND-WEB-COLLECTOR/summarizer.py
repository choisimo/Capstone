from __future__ import annotations
"""
summarizer.py

Lightweight summarization & fact extraction pipeline.
Feature-flag controlled via env SUMMARY_ENABLED (default 1) and SUMMARY_LLM_ENABLED (default 0).
Falls back to heuristic summarizer if no LLM.

Produces summary event dictionaries (NOT published here). Caller publishes.
"""
import os
import re
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

MAX_SUMMARY_LEN = int(os.getenv("SUMMARY_MAX_CHARS", "400"))
KEY_POINTS_MAX = int(os.getenv("SUMMARY_KEYPOINTS_MAX", "5"))
ENABLE = os.getenv("SUMMARY_ENABLED", "1") in ("1", "true", "True")
LLM_ENABLE = os.getenv("SUMMARY_LLM_ENABLED", "0") in ("1", "true", "True")

_amount_re = re.compile(r"(\d{1,3}(?:,\d{3})*)(?:\s*)(억원|조|만원|원)?")
_ratio_re = re.compile(r"(\d{1,3}(?:\.\d+)?%)")
_date_re = re.compile(r"(20\d{2}[./-](?:0?[1-9]|1[0-2])[./-](?:0?[1-9]|[12]\d|3[01]))")
_org_re = re.compile(r"([가-힣A-Za-z]{2,20}?(?:공단|위원회|부|처|청|원|센터|연구원|협회|공사|회사|은행|증권))")


class LLMClient:
    def __init__(self):
        self.model = os.getenv("SUMMARY_LLM_MODEL", "mock")

    def summarize(self, text: str, topic: str) -> Tuple[str, List[str]]:
        # Placeholder: In real impl, call provider API.
        # Keep deterministic for tests.
        t = text.strip().replace("\n", " ")
        if len(t) > MAX_SUMMARY_LEN:
            t_short = t[:MAX_SUMMARY_LEN]
        else:
            t_short = t
        # Naive key points split by sentence.
        sents = re.split(r"(?<=[.!?。])\s+", t_short)
        key_points = [s.strip() for s in sents if s.strip()][:KEY_POINTS_MAX]
        summary = key_points[0] if key_points else t_short[:MAX_SUMMARY_LEN]
        return summary, key_points


def heuristic_summarize(text: str) -> Tuple[str, List[str]]:
    txt = (text or "").strip()
    if not txt:
        return "", []
    # Sentences by period / newline
    parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", txt)
    parts_clean = [p.strip() for p in parts if p.strip()]
    key_points = parts_clean[:KEY_POINTS_MAX]
    # Summary is first sentence truncated
    summary = key_points[0][:MAX_SUMMARY_LEN] if key_points else txt[:MAX_SUMMARY_LEN]
    return summary, key_points


def extract_facts(text: str) -> Dict[str, List[str]]:
    amounts = sorted({m.group(0).strip() for m in _amount_re.finditer(text)})
    ratios = sorted({m.group(1).strip() for m in _ratio_re.finditer(text)})
    dates = sorted({m.group(1).strip() for m in _date_re.finditer(text)})
    orgs = sorted({m.group(1).strip() for m in _org_re.finditer(text)})
    return {
        "amounts": amounts[:20],
        "ratios": ratios[:20],
        "dates": dates[:20],
        "orgs": orgs[:20],
    }


def build_summary_event(raw_evt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not ENABLE:
        return None
    text = raw_evt.get("text") or ""
    meta = raw_evt.get("meta", {}) or {}
    topic = meta.get("keyword") or os.getenv("SUMMARY_TOPIC", "국민연금")

    if not text.strip():
        return None

    if LLM_ENABLE:
        client = LLMClient()
        summary, key_points = client.summarize(text, topic)
        model_used = client.model
    else:
        summary, key_points = heuristic_summarize(text)
        model_used = "heuristic"

    facts = extract_facts(text)

    evt = {
        "id": str(uuid.uuid4()),
        "raw_id": raw_evt.get("id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "key_points": key_points,
        "facts": facts,
        "meta": {
            "model": model_used,
            "input_chars": len(text),
            "lang": meta.get("lang", "ko"),
            "seed_url": meta.get("seed_url"),
            "url_norm": meta.get("url_norm"),
            "topic": topic,
            "source": raw_evt.get("source"),
            "channel": raw_evt.get("channel"),
        },
    }
    return evt
