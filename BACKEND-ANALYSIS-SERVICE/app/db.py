from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from .config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_db = None


async def init_db() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_db():
    if _db is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    return _db