from typing import Dict, Any, List
from fastapi import APIRouter, Query
from app.services.orchestrator_service import orchestrator
from app.models import TaskStatus

router = APIRouter()


def _safe_sentiment(value: str) -> str:
    v = (value or "").lower()
    return v if v in {"positive", "negative", "neutral"} else "neutral"


def _task_mentions(task_id: str) -> int:
    if task_id in orchestrator.results:
        return len(orchestrator.results[task_id])
    return 0


def _majority_sentiment(task_id: str, fallback: str = "neutral") -> str:
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    if task_id in orchestrator.results:
        for r in orchestrator.results[task_id]:
            s = r.data.get("sentiment") if isinstance(r.data, dict) else None
            s = _safe_sentiment(s) if s else None
            if s:
                counts[s] += 1
    total = sum(counts.values())
    if total == 0:
        return _safe_sentiment(fallback)
    # majority
    return max(counts.items(), key=lambda kv: kv[1])[0]


@router.get("/dashboard/overview")
async def get_dashboard_overview() -> Dict[str, Any]:
    tasks = list(orchestrator.tasks.values())

    # Mentions from results
    total_mentions = 0
    pos, neg, neu = 0, 0, 0

    for t in tasks:
        m = _task_mentions(t.id)
        total_mentions += m
        # derive sentiment
        fallback = (t.metadata or {}).get("sentiment", "neutral")
        s = _majority_sentiment(t.id, fallback=fallback)
        if s == "positive":
            pos += 1
        elif s == "negative":
            neg += 1
        else:
            neu += 1

    denom = max(1, pos + neg + neu)
    positive_ratio = pos / denom
    negative_ratio = neg / denom

    active_issues = sum(1 for t in tasks if t.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED})

    return {
        "total_mentions": total_mentions,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "active_issues": active_issues,
        "alerts": {"warning": 0, "critical": 0},
        "channels": [],
        "metadata": {"source": "orchestrator", "generated": True},
    }


@router.get("/issues/top")
async def get_top_issues(limit: int = Query(default=4, ge=1, le=20)) -> Dict[str, List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []

    # Build issue candidates from tasks
    for t in orchestrator.tasks.values():
        mentions = _task_mentions(t.id)
        fallback = (t.metadata or {}).get("sentiment", "neutral")
        sentiment = _majority_sentiment(t.id, fallback=fallback)
        title = t.metadata.get("title") if isinstance(t.metadata, dict) else None
        if not title:
            # fallback title from keywords or task type
            if t.keywords:
                title = " ".join(t.keywords)
            else:
                title = t.task_type.value.replace("_", " ")
        category = (t.metadata or {}).get("category", "기타")

        items.append({
            "id": t.id,
            "title": title,
            "sentiment": sentiment,
            "mentions": mentions,
            "trend": "stable",
            "category": category,
        })

    # Sort by mentions desc, fallback created_at asc
    items.sort(key=lambda x: (-x["mentions"]))

    return {"items": items[:limit]}
