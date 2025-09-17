from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from ..db import get_db

router = APIRouter()


@router.get("/personas")
async def list_personas(
    limit: int = Query(default=20, ge=1, le=200),
    min_posts: int = Query(default=1, ge=1),
):
    db = get_db()
    pipeline = [
        {"$match": {"author_hash": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$author_hash",
            "count": {"$sum": 1},
            "last_seen": {"$max": "$created_at"},
        }},
        {"$match": {"count": {"$gte": min_posts}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    rows = [r async for r in db.raw_posts.aggregate(pipeline)]
    items = [
        {
            "author_hash": r["_id"],
            "posts": r["count"],
            "last_seen": r.get("last_seen"),
        }
        for r in rows
    ]
    return {"total": len(items), "items": items}


@router.get("/personas/{author_hash}")
async def get_persona(author_hash: str, top_k_keywords: int = 20):
    db = get_db()

    # basic counts
    total = await db.raw_posts.count_documents({"author_hash": author_hash})

    # by source/channel
    pipeline_sc = [
        {"$match": {"author_hash": author_hash}},
        {"$group": {"_id": {"s": "$source", "c": "$channel"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    sc = [r async for r in db.raw_posts.aggregate(pipeline_sc)]
    by_source = [
        {"source": r["_id"]["s"], "channel": r["_id"]["c"], "count": r["n"]}
        for r in sc
    ]

    # sentiment distribution
    pipeline_sent = [
        {"$match": {"author_hash": author_hash, "meta.sentiment": {"$exists": True}}},
        {"$group": {"_id": "$meta.sentiment", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    sent = [r async for r in db.raw_posts.aggregate(pipeline_sent)]
    sentiment = {str(r["_id"]): r["n"] for r in sent}

    # keywords aggregation
    pipeline_kw = [
        {"$match": {"author_hash": author_hash, "meta.keywords": {"$exists": True}}},
        {"$project": {"k": "$meta.keywords"}},
        {"$unwind": "$k"},
        {"$group": {"_id": "$k", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": top_k_keywords},
    ]
    kws = [r async for r in db.raw_posts.aggregate(pipeline_kw)]
    top_keywords = [{"keyword": r["_id"], "count": r["n"]} for r in kws]

    # samples
    cursor = db.raw_posts.find({"author_hash": author_hash}).sort("created_at", -1).limit(5)
    samples: List[Dict[str, Any]] = []
    async for d in cursor:
        samples.append({
            "id": d.get("id"),
            "source": d.get("source"),
            "channel": d.get("channel"),
            "url": d.get("url"),
            "text": d.get("text"),
            "created_at": d.get("created_at"),
        })

    return {
        "author_hash": author_hash,
        "total_posts": total,
        "by_source": by_source,
        "sentiment": sentiment,
        "top_keywords": top_keywords,
        "samples": samples,
    }
