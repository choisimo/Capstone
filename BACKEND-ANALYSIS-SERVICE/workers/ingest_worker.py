from __future__ import annotations

import os
import json
import time
import hashlib
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

try:
    from confluent_kafka import Consumer, Producer  # type: ignore
    HAS_KAFKA = True
except Exception:
    HAS_KAFKA = False

try:
    from prometheus_client import Counter, Histogram, start_http_server  # type: ignore
    HAS_PROM = True
except Exception:
    HAS_PROM = False

try:
    import sentry_sdk  # type: ignore
    HAS_SENTRY = True
except Exception:
    HAS_SENTRY = False


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "analysis")

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")
KAFKA_GROUP = os.getenv("INGEST_GROUP", "analysis-ingest")
RAW_TOPIC = os.getenv("RAW_TOPIC", "raw.posts.v1")
SEED_TOPIC = os.getenv("SEED_TOPIC", "seed.news.v1")
CLEAN_TOPIC = os.getenv("CLEAN_TOPIC", "clean.posts.v1")
SENTI_TOPIC = os.getenv("SCORES_TOPIC", "scores.sentiment.v1")

METRICS_PORT = int(os.getenv("INGEST_METRICS_PORT", "0") or 0)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

_C_CONSUME = None
_C_PRODUCE = None
_H_LAT = None


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _norm_text(s: str) -> str:
    return " ".join((s or "").split())[:8000]


def _dedup_key(post: Dict[str, Any]) -> str:
    meta = post.get("meta", {}) or {}
    base = "|".join([
        str(post.get("source") or ""),
        str(post.get("channel") or ""),
        str(meta.get("url_norm") or post.get("url") or ""),
        str(post.get("author_hash") or ""),
        _hash(_norm_text(post.get("text") or ""))[:16],
    ])
    return _hash(base)


async def handle_seed(db, evt: Dict[str, Any]) -> None:
    col = db.seeds
    url_norm = (evt.get("meta", {}) or {}).get("url_norm") or evt.get("url")
    doc = {
        "id": evt.get("id"),
        "url": evt.get("url"),
        "url_norm": url_norm,
        "title": evt.get("text"),
        "source": evt.get("source"),
        "channel": evt.get("channel"),
        "created_at": evt.get("created_at"),
        "meta": evt.get("meta", {}),
        "ts_ingested": time.time(),
    }
    await col.update_one({"url_norm": url_norm}, {"$set": doc}, upsert=True)


async def handle_raw(db, evt: Dict[str, Any], producer: Optional[Producer]) -> None:
    col = db.raw_posts
    evt["text_norm"] = _norm_text(evt.get("text") or "")
    evt["dedup_key"] = _dedup_key(evt)
    evt["ts_ingested"] = time.time()
    await col.update_one({"dedup_key": evt["dedup_key"]}, {"$set": evt}, upsert=True)

    # Emit clean.posts.v1
    clean = {
        "id": evt["id"],
        "text_norm": evt["text_norm"],
        "pii_flags": {},
        "dedup_key": evt["dedup_key"],
        "created_at": evt.get("created_at"),
        "source": evt.get("source"),
        "channel": evt.get("channel"),
    }
    if producer and HAS_KAFKA:
        try:
            producer.produce(CLEAN_TOPIC, json.dumps(clean, ensure_ascii=False).encode("utf-8"))
            if _C_PRODUCE:
                _C_PRODUCE.labels(topic=CLEAN_TOPIC).inc()
        except Exception:
            pass

    # Emit scores.sentiment.v1 if present
    meta = evt.get("meta", {}) or {}
    if meta.get("sentiment") is not None:
        scores_evt = {
            "post_id": evt["id"],
            "label3": meta.get("sentiment"),
            "label8": None,
            "scores": {"model": float(meta.get("sentiment_score") or 0.0)},
            "model_ver": "hf-inline",
            "infer_ts": time.time(),
        }
        if producer and HAS_KAFKA:
            try:
                producer.produce(SENTI_TOPIC, json.dumps(scores_evt, ensure_ascii=False).encode("utf-8"))
                if _C_PRODUCE:
                    _C_PRODUCE.labels(topic=SENTI_TOPIC).inc()
            except Exception:
                pass


def _make_consumer() -> Optional[Consumer]:
    if not HAS_KAFKA:
        print("[ingest-worker] Kafka not available. Set up confluent-kafka.")
        return None
    conf = {
        "bootstrap.servers": KAFKA_BROKERS,
        "group.id": KAFKA_GROUP,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    }
    return Consumer(conf)


def _make_producer() -> Optional[Producer]:
    if not HAS_KAFKA:
        return None
    return Producer({"bootstrap.servers": KAFKA_BROKERS})


def main() -> None:
    if HAS_SENTRY and SENTRY_DSN:
        try:
            sentry_sdk.init(dsn=SENTRY_DSN)
        except Exception:
            pass

    if HAS_PROM and METRICS_PORT:
        try:
            global _C_CONSUME, _C_PRODUCE, _H_LAT
            _C_CONSUME = Counter("ingest_messages_total", "Messages consumed", ["topic"])  # type: ignore
            _C_PRODUCE = Counter("ingest_messages_produced_total", "Messages produced", ["topic"])  # type: ignore
            _H_LAT = Histogram("ingest_handle_seconds", "Event handle latency seconds")  # type: ignore
            start_http_server(METRICS_PORT)  # type: ignore
        except Exception:
            pass

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    cons = _make_consumer()
    prod = _make_producer()

    if cons is None:
        print("[ingest-worker] Exiting: Kafka consumer unavailable.")
        return

    cons.subscribe([RAW_TOPIC, SEED_TOPIC])
    print(f"[ingest-worker] started; consuming {RAW_TOPIC}, {SEED_TOPIC}")
    try:
        while True:
            msg = cons.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                continue
            topic = msg.topic()
            try:
                evt = json.loads(msg.value().decode("utf-8"))
            except Exception:
                continue
            t0 = time.time()
            try:
                if topic == SEED_TOPIC:
                    import asyncio
                    asyncio.run(handle_seed(db, evt))
                elif topic == RAW_TOPIC:
                    import asyncio
                    asyncio.run(handle_raw(db, evt, prod))
                if _C_CONSUME:
                    _C_CONSUME.labels(topic=topic).inc()
            finally:
                if _H_LAT:
                    _H_LAT.observe(max(0.0, time.time() - t0))
    except KeyboardInterrupt:
        pass
    finally:
        try:
            cons.close()
        except Exception:
            pass
        client.close()
        print("[ingest-worker] stopped")


if __name__ == "__main__":
    main()
