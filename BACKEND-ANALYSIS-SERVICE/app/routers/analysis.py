from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Query
from ..db import get_db

from ..schemas import (
    ArticlesResponse,
    ChatRequest,
    ChatResponse,
    DocumentsResponse,
    GenerateReportRequest,
    GenerateReportResponse,
    MeshResponse,
    MeshMeta,
    MeshWindow,
)

router = APIRouter()


@router.get("/mesh-data", response_model=MeshResponse)
async def get_mesh_data(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    source: list[str] | None = Query(default=None),
    channel: list[str] | None = Query(default=None),
    lang: list[str] | None = Query(default=None),
    keywords: list[str] | None = Query(default=None),
    persona: list[str] | None = Query(default=None),
    emotion: list[str] | None = Query(default=None),
    experience: list[str] | None = Query(default=None),
    agg: str = Query(default="day", pattern="^(hour|day|week)$"),
    min_weight: float | None = None,
    max_nodes: int | None = Query(default=200),
    scope: str = Query(default="global", pattern="^(global|article)$"),
    article_id: Optional[str] = None,
):
    """Build a lightweight mesh: seed nodes connected to related raw posts (web/youtube/article/comment)
    via meta.seed_id. Window defaults to last 3 days.
    """
    db = get_db()
    now = datetime.utcnow()
    if to is None:
        to = now
    if from_ is None:
        from_ = to - timedelta(days=3)

    window = MeshWindow(from_=from_, to=to, agg=agg)  # type: ignore[arg-type]
    filters: Dict[str, Any] = {}
    if source:
        filters["source"] = source
    if channel:
        filters["channel"] = channel
    meta = MeshMeta(window=window, filters=filters, computed_at=now)

    # 1) Load seed nodes in window
    seed_rows: List[Dict[str, Any]] = [
        r async for r in db.seeds.aggregate([
            {"$addFields": {"ts": {"$dateFromString": {"dateString": "$created_at"}}}},
            {"$match": {"ts": {"$gte": from_, "$lte": to}}},
            {"$sort": {"ts": -1}},
            {"$limit": int(max_nodes or 200)},
        ])
    ]
    seed_ids = [s.get("id") for s in seed_rows if s.get("id")]

    # 2) Load related posts linked by meta.seed_id
    match_posts: Dict[str, Any] = {"meta.seed_id": {"$in": seed_ids}}
    if source:
        match_posts["source"] = {"$in": source}
    if channel:
        match_posts["channel"] = {"$in": channel}

    post_rows: List[Dict[str, Any]] = [
        r async for r in db.raw_posts.aggregate([
            {"$addFields": {"ts": {"$dateFromString": {"dateString": "$created_at"}}}},
            {"$match": {"ts": {"$gte": from_, "$lte": to}}},
            {"$match": match_posts},
            {"$project": {
                "id": 1,
                "source": 1,
                "channel": 1,
                "text": 1,
                "meta": 1,
                "dedup_key": 1,
            }},
            {"$limit": int(max_nodes or 200)},
        ])
    ]

    # 3) Build nodes & links
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    node_ids: set[str] = set()

    for s in seed_rows:
        sid = f"seed:{s.get('id')}"
        if sid not in node_ids:
            nodes.append({"id": sid, "type": "seed", "label": (s.get("title") or s.get("url") or "seed")[:80]})
            node_ids.add(sid)

    for p in post_rows:
        did = p.get("dedup_key") or p.get("id")
        if not did:
            continue
        nid = f"doc:{did}"
        if nid not in node_ids:
            label = (p.get("meta", {}) or {}).get("video_title") or (p.get("meta", {}) or {}).get("title") or (p.get("channel") or p.get("source") or "doc")
            nodes.append({"id": nid, "type": str(p.get("channel") or p.get("source") or "doc"), "label": str(label)[:80]})
            node_ids.add(nid)
        sid = p.get("meta", {}).get("seed_id")
        if sid:
            links.append({"source": f"seed:{sid}", "target": nid, "weight": 1.0})

    return MeshResponse(nodes=nodes, links=links, meta=meta)


@router.get("/articles", response_model=ArticlesResponse)
async def list_articles(
    q: Optional[str] = None,
    source: list[str] | None = Query(default=None),
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    page: int = 1,
    size: int = 20,
    sort: str = Query(default="recency", pattern="^(recency|popularity)$"),
):
    return ArticlesResponse(total=0, items=[], agg={})


@router.get("/articles/{article_id}/mesh-data", response_model=MeshResponse)
async def get_article_mesh_data(article_id: str, min_weight: float | None = None, max_nodes: int | None = None):
    now = datetime.utcnow()
    window = MeshWindow(from_=now, to=now, agg="day")
    meta = MeshMeta(window=window, filters={"article_id": article_id}, computed_at=now)
    return MeshResponse(nodes=[], links=[], meta=meta)


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    q: Optional[str] = None,
    article_id: Optional[str] = None,
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    lang: list[str] | None = Query(default=None),
    persona: list[str] | None = Query(default=None),
    emotion: list[str] | None = Query(default=None),
    experience: list[str] | None = Query(default=None),
    keywords: list[str] | None = Query(default=None),
    page: int = 1,
    size: int = 20,
):
    return DocumentsResponse(total=0, items=[])


@router.post("/generate-report", response_model=GenerateReportResponse)
async def generate_report(req: GenerateReportRequest):
    return GenerateReportResponse(report_id="stub-1", markdown="# Report\n\nTBD", citations=[], meta={})


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return ChatResponse(reply="This is a stub reply.", sources=[], route="rag")


# ---------------- Analytics Endpoints ----------------

@router.get("/analytics/sentiment-trend")
async def sentiment_trend(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    source: list[str] | None = Query(default=None),
    channel: list[str] | None = Query(default=None),
    agg: str = Query(default="day", pattern="^(hour|day|week)$"),
    limit: int = Query(default=200, ge=1, le=2000),
):
    """Aggregate sentiment counts over time buckets from raw_posts.meta.sentiment.
    Returns series of { ts, pos, neg, neu }.
    """
    db = get_db()
    start = datetime.utcnow()
    if to is None:
        to = datetime.utcnow()
    if from_ is None:
        # default: 7 days window
        from_ = to - timedelta(days=7)

    bucket = {"unit": agg}
    # Map to Mongo $dateTrunc units
    unit_map = {"hour": "hour", "day": "day", "week": "week"}
    bucket_unit = unit_map.get(agg, "day")

    match: Dict[str, Any] = {}
    if source:
        match["source"] = {"$in": source}
    if channel:
        match["channel"] = {"$in": channel}

    pipeline: List[Dict[str, Any]] = [
        {"$match": match},
        {"$addFields": {
            "ts": {"$dateFromString": {"dateString": "$created_at"}},
            "sent": "$meta.sentiment",
        }},
        {"$match": {"ts": {"$gte": from_, "$lte": to}}},
        {"$addFields": {"ts_bucket": {"$dateTrunc": {"date": "$ts", "unit": bucket_unit}}}},
        {"$group": {"_id": {"ts": "$ts_bucket", "sent": "$sent"}, "n": {"$sum": 1}}},
        {"$sort": {"_id.ts": 1}},
        {"$limit": limit * 3},
    ]

    rows = [r async for r in db.raw_posts.aggregate(pipeline)]

    # Pivot into {ts -> {pos,neg,neu}}
    series_map: Dict[str, Dict[str, int]] = {}
    total = 0
    for r in rows:
        ts = r["_id"]["ts"]
        sent = str(r["_id"].get("sent") or "neutral").lower()
        if isinstance(ts, datetime):
            ts_iso = ts.replace(microsecond=0).isoformat() + "Z"
        else:
            ts_iso = str(ts)
        if ts_iso not in series_map:
            series_map[ts_iso] = {"positive": 0, "negative": 0, "neutral": 0}
        if sent not in ("positive", "negative", "neutral"):
            sent = "neutral"
        series_map[ts_iso][sent] += int(r.get("n", 0))
        total += int(r.get("n", 0))

    series = [
        {"ts": ts, "pos": v.get("positive", 0), "neg": v.get("negative", 0), "neu": v.get("neutral", 0)}
        for ts, v in sorted(series_map.items(), key=lambda x: x[0])
    ]
    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    return {"series": series, "meta": {"hits": total, "latency_ms": elapsed_ms}}


@router.get("/analytics/top-keywords")
async def top_keywords(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    source: list[str] | None = Query(default=None),
    channel: list[str] | None = Query(default=None),
    size: int = Query(default=30, ge=1, le=200),
):
    """Aggregate top keywords from raw_posts.meta.keywords."""
    db = get_db()
    if to is None:
        to = datetime.utcnow()
    if from_ is None:
        from_ = to - timedelta(days=7)

    match: Dict[str, Any] = {}
    if source:
        match["source"] = {"$in": source}
    if channel:
        match["channel"] = {"$in": channel}

    pipeline: List[Dict[str, Any]] = [
        {"$match": match},
        {"$addFields": {"ts": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$match": {"ts": {"$gte": from_, "$lte": to}}},
        {"$match": {"meta.keywords": {"$exists": True}}},
        {"$project": {"k": "$meta.keywords"}},
        {"$unwind": "$k"},
        {"$group": {"_id": "$k", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": size},
    ]
    rows = [r async for r in db.raw_posts.aggregate(pipeline)]
    items = [{"keyword": r["_id"], "count": r["n"]} for r in rows]
    return {"total": len(items), "items": items}


@router.get("/sentiments")
async def sentiments(
    q: Optional[str] = None,
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    source: list[str] | None = Query(default=None),
    channel: list[str] | None = Query(default=None),
    age_band: Optional[str] = None,
    group_by: str = Query(default="channel", pattern="^(issue|age|channel)$"),
):
    """Return sentiment summary and time series per API contract.
    Uses raw_posts.meta.sentiment and buckets by day.
    """
    db = get_db()
    start = datetime.utcnow()
    if to is None:
        to = datetime.utcnow()
    if from_ is None:
        from_ = to - timedelta(days=7)

    match: Dict[str, Any] = {}
    if source:
        match["source"] = {"$in": source}
    if channel:
        match["channel"] = {"$in": channel}

    pipeline: List[Dict[str, Any]] = [
        {"$match": match},
        {"$addFields": {
            "ts": {"$dateFromString": {"dateString": "$created_at"}},
            "sent": {"$toLower": {"$ifNull": ["$meta.sentiment", "neutral"]}},
        }},
        {"$match": {"ts": {"$gte": from_, "$lte": to}}},
        {"$addFields": {"ts_bucket": {"$dateTrunc": {"date": "$ts", "unit": "day"}}}},
        {"$group": {"_id": {"ts": "$ts_bucket", "sent": "$sent"}, "n": {"$sum": 1}}},
        {"$sort": {"_id.ts": 1}},
    ]
    rows = [r async for r in db.raw_posts.aggregate(pipeline)]

    series_map: Dict[str, Dict[str, int]] = {}
    total = 0
    for r in rows:
        ts = r["_id"]["ts"]
        sent = str(r["_id"].get("sent") or "neutral").lower()
        ts_iso = (ts.replace(microsecond=0).isoformat() + "Z") if isinstance(ts, datetime) else str(ts)
        if ts_iso not in series_map:
            series_map[ts_iso] = {"positive": 0, "negative": 0, "neutral": 0}
        if sent not in ("positive", "negative", "neutral"):
            sent = "neutral"
        series_map[ts_iso][sent] += int(r.get("n", 0))
        total += int(r.get("n", 0))

    sum_pos = sum(v["positive"] for v in series_map.values())
    sum_neg = sum(v["negative"] for v in series_map.values())
    sum_neu = sum(v["neutral"] for v in series_map.values())
    denom = max(1, sum_pos + sum_neg + sum_neu)
    summary = {"pos": round(sum_pos / denom, 4), "neg": round(sum_neg / denom, 4), "neu": round(sum_neu / denom, 4)}

    series = [
        {"ts": ts, "pos": v.get("positive", 0), "neg": v.get("negative", 0), "neu": v.get("neutral", 0)}
        for ts, v in sorted(series_map.items(), key=lambda x: x[0])
    ]

    emotions: Dict[str, float] = {}
    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    return {"summary": summary, "emotions": emotions, "series": series, "meta": {"hits": total, "latency_ms": elapsed_ms}}