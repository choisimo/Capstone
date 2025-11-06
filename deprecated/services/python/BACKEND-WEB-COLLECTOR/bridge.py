from __future__ import annotations
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from .config import ChangeDetectionConfig, BusConfig, BridgeConfig
from .cdio_client import ChangeDetectionClient
from .publishers import make_publisher
from .state import CollectorState


def norm_url(u: str) -> str:
    # simple normalization: strip fragments and trailing slashes
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(u)
        path = parts.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))
    except Exception:
        return u


def hash_key(s: str) -> bytes:
    return hashlib.sha256(s.encode("utf-8")).digest()


def build_event_raw_post(watch: Dict[str, Any], content: str, cfg: BridgeConfig) -> Dict[str, Any]:
    url = watch.get("url", "")
    url_n = norm_url(url)
    now = datetime.now(timezone.utc)
    eid = str(uuid.uuid4())
    # Minimal schema mapping per CONTRACTS raw.posts.v1
    evt = {
        "id": eid,
        "source": cfg.source,
        "channel": cfg.channel,
        "url": url,
        "author_hash": "",  # unknown for web pages
        "text": content,
        "lang": "",  # leave empty; downstream can detect
        "created_at": now.isoformat(),
        "meta": {
            "url_norm": url_n,
            "platform_profile": cfg.platform_profile,
            "watch_uuid": watch.get("uuid"),
            "title": watch.get("title"),
        },
    }
    return evt


def main() -> None:
    cd_cfg = ChangeDetectionConfig.from_env()
    bus_cfg = BusConfig.from_env()
    br_cfg = BridgeConfig.from_env()

    client = ChangeDetectionClient(cd_cfg.base_url, cd_cfg.api_key)
    publisher = make_publisher(bus_cfg.bus, bus_cfg.kafka_brokers, bus_cfg.pubsub_project)
    state = CollectorState.load(br_cfg.state_path)

    print(
        json.dumps(
            {
                "msg": "collector bridge starting",
                "bus": bus_cfg.bus,
                "topic": bus_cfg.raw_topic,
                "cd_base": cd_cfg.base_url,
                "poll": br_cfg.poll_interval_sec,
            }
        )
    )

    while True:
        try:
            watches = client.list_watches(tag=br_cfg.watch_tag)
            for uuid_str, w in watches.items():
                if not isinstance(w, dict):
                    continue
                w["uuid"] = uuid_str
                hist = client.get_watch_history(uuid_str)
                if not hist:
                    continue
                # history is dict[timestamp->path]; choose latest key
                latest_ts = sorted(hist.keys())[-1]
                last_done = state.last_ts.get(uuid_str)
                if last_done and latest_ts <= last_done:
                    continue
                content = client.get_snapshot(uuid_str, "latest", html=br_cfg.include_html)
                evt = build_event_raw_post(w, content, br_cfg)

                headers = {
                    "trace_id": str(uuid.uuid4()),
                    "schema_version": "raw.posts.v1",
                    "source": br_cfg.source,
                    "channel": br_cfg.channel,
                    "content_type": "text/html" if br_cfg.include_html else "text/plain",
                    "platform_profile": br_cfg.platform_profile,
                }
                key = hash_key(f"{br_cfg.source}:{evt['meta']['url_norm']}")
                data = json.dumps(evt, ensure_ascii=False).encode("utf-8")
                res = publisher.publish(bus_cfg.raw_topic, key=key, value=data, headers=headers)
                if res.ok:
                    state.last_ts[uuid_str] = latest_ts
                    state.save(br_cfg.state_path)
                else:
                    print(json.dumps({"warn": "publish failed", "err": res.error}))
            time.sleep(br_cfg.poll_interval_sec)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            time.sleep(min(60, br_cfg.poll_interval_sec))


if __name__ == "__main__":
    main()
