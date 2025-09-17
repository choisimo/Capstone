from __future__ import annotations

from typing import Optional
from pymongo import ASCENDING, DESCENDING  # type: ignore

from motor.motor_asyncio import AsyncIOMotorClient

from .config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_db = None


async def init_db() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]
    # Create indexes helpful for queries/analytics
    try:
        # seeds: lookups by url_norm, created_at
        await _db.seeds.create_index([("url_norm", ASCENDING)], name="ix_seeds_url_norm", unique=True)
        await _db.seeds.create_index([("created_at", ASCENDING)], name="ix_seeds_created_at")
        # raw_posts: dedup and filters
        await _db.raw_posts.create_index([("dedup_key", ASCENDING)], name="ix_raw_dedup", unique=True)
        await _db.raw_posts.create_index([("author_hash", ASCENDING)], name="ix_raw_author")
        await _db.raw_posts.create_index([("meta.url_norm", ASCENDING)], name="ix_raw_url_norm")
        await _db.raw_posts.create_index([("source", ASCENDING), ("channel", ASCENDING)], name="ix_raw_source_channel")
        await _db.raw_posts.create_index([("created_at", ASCENDING)], name="ix_raw_created_at")
    except Exception:
        # Index creation best-effort
        pass


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_db():
    if _db is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    return _db