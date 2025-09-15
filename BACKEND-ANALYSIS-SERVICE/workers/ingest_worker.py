from __future__ import annotations

import asyncio
import os
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "analysis")


async def main() -> None:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    print("[ingest-worker] started; awaiting messages (stub)")

    try:
        while True:
            # TODO: consume raw.posts.v1, normalize, dedup, write to Mongo/Vector
            await asyncio.sleep(5)
            print("[ingest-worker] heartbeat: no-op in stub mode")
    except asyncio.CancelledError:
        pass
    finally:
        client.close()
        print("[ingest-worker] stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
