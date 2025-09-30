#!/usr/bin/env python3
"""History log generator.

Creates markdown history files under `DOCUMENTS/HISTORY/` following the
`history-log-prompt.md` structure. Users supply section contents via CLI
flags; sections left unspecified are filled with TODO placeholders so that
manual edits can happen after file creation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
from typing import Iterable, List

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_DIR = REPO_ROOT / "DOCUMENTS" / "HISTORY"
DEFAULT_TITLE = "TBD"


def kst_now() -> dt.datetime:
    tz = ZoneInfo("Asia/Seoul") if ZoneInfo else dt.timezone(dt.timedelta(hours=9))
    return dt.datetime.now(tz)


def timestamp_slug(now: dt.datetime) -> str:
    return now.strftime("%Y%m%d-%H%M%S")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a history log entry")
    parser.add_argument("--summary", required=True, help="One-line summary sentence")
    parser.add_argument(
        "--purpose",
        action="append",
        default=[],
        help="Purpose bullet, use 'Title: details'. Repeatable",
    )
    parser.add_argument(
        "--change",
        action="append",
        default=[],
        help="Change details bullet, use 'Title: details'. Repeatable",
    )
    parser.add_argument(
        "--impact",
        action="append",
        default=[],
        help="Impacted service bullet, use 'Title: details'. Repeatable",
    )
    parser.add_argument(
        "--modified",
        action="append",
        default=[],
        help="Modified file bullet, use 'path/to/file: details'. Repeatable",
    )
    parser.add_argument(
        "--verification",
        action="append",
        default=[],
        help="Verification bullet, use 'Command: result'. Repeatable",
    )
    parser.add_argument(
        "--followup",
        action="append",
        default=[],
        help="Follow-up bullet, use 'Title: details'. Repeatable",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting file if it already exists",
    )
    return parser.parse_args(argv)


def ensure_bullets(items: Iterable[str], fallback: str) -> List[str]:
    formatted: List[str] = []
    for raw in items:
        raw = raw.strip()
        if not raw:
            continue
        if ":" in raw:
            title, desc = raw.split(":", 1)
            title = title.strip() or DEFAULT_TITLE
            desc = desc.strip() or fallback
        else:
            title = DEFAULT_TITLE
            desc = raw
        formatted.append(f"- **{title}**: {desc}")
    if not formatted:
        formatted.append(f"- **{DEFAULT_TITLE}**: {fallback}")
    return formatted


def build_document(args: argparse.Namespace, now: dt.datetime) -> str:
    lines = ["# Summary", args.summary.strip(), "", "## Purpose"]
    lines.extend(ensure_bullets(args.purpose, "Purpose to be detailed"))
    lines.extend(["", "## Change Details"])
    lines.extend(ensure_bullets(args.change, "Describe implemented changes"))
    lines.extend(["", "## Impacted Services"])
    lines.extend(ensure_bullets(args.impact, "List impacted services"))
    lines.extend(["", "## Modified Files"])
    lines.extend(ensure_bullets(args.modified, "Add modified files"))
    lines.extend(["", "## Verification"])
    lines.extend(ensure_bullets(args.verification, "List verification steps or reasons"))
    lines.extend(["", "## Follow-up Actions"])
    lines.extend(ensure_bullets(args.followup, "List remaining TODOs"))
    lines.extend(["", f"Last-Updated: {now.strftime('%Y-%m-%d %H:%M KST')}", ""])
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    now = kst_now()
    slug = timestamp_slug(now)
    ensure_directory(HISTORY_DIR)
    target = HISTORY_DIR / f"{slug}-history.md"
    if target.exists() and not args.overwrite:
        print(f"History file already exists: {target}")
        return 1

    content = build_document(args, now)
    target.write_text(content, encoding="utf-8")
    rel_path = target.relative_to(REPO_ROOT)
    print(f"History log created: {rel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
