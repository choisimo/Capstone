from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CollectorState:
    # watch_uuid -> last_timestamp_processed (str)
    last_ts: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def load(path: str) -> "CollectorState":
        if not os.path.exists(path):
            return CollectorState()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return CollectorState(last_ts=data.get("last_ts", {}))
        except Exception:
            return CollectorState()

    def save(self, path: str) -> None:
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"last_ts": self.last_ts}, f, ensure_ascii=False)
        os.replace(tmp, path)
