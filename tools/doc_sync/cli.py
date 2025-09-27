#!/usr/bin/env python3
"""
DocSync CLI

Lightweight, dependency-free "check" mode for CI/pre-commit. Optional "write" mode prepares
front-matter headers and can be extended to use LangChain/LangGraph pipelines.

- check: verifies required documentation files contain DocSync metadata headers
         and basic freshness signals.
- write: initializes/updates metadata headers (non-invasive) and records current HEAD SHA.

This file intentionally avoids non-stdlib imports so it can run inside validate_project.sh
without extra pip installs. Advanced features should be implemented in modules that import
optional dependencies inside functions (see graph.py/llm.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List

# Constants
REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_DOC = REPO_ROOT / ".windsurf/workflows/documentation-sync-workflow.md"
FRONT_MATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"


def is_excluded(path: Path) -> bool:
    """Exclude common non-doc directories."""
    excluded = {"node_modules", ".git", "venv", ".venv", "env", "__pycache__"}
    return any(part in excluded for part in path.parts)


def get_target_docs() -> List[Path]:
    """Collect target markdown docs across the repo.

    Includes:
    - .windsurf/workflows/*.md (always, including REQUIRED_DOC)
    - docs/**/*.md under repo root
    - Service READMEs and service docs under known service directories
    - Root README.md if present
    """
    targets: List[Path] = []

    # Always include REQUIRED_DOC
    targets.append(REQUIRED_DOC)

    # Root README
    readme = REPO_ROOT / "README.md"
    if readme.exists():
        targets.append(readme)

    # Workflow docs
    wf_dir = REPO_ROOT / ".windsurf/workflows"
    if wf_dir.exists():
        for p in wf_dir.glob("*.md"):
            if p.is_file() and not is_excluded(p):
                targets.append(p)

    # Root docs/**
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        for p in docs_dir.rglob("*.md"):
            if p.is_file() and not is_excluded(p):
                targets.append(p)

    # Known service directories
    service_dirs = [
        REPO_ROOT / "BACKEND-ABSA-SERVICE",
        REPO_ROOT / "BACKEND-COLLECTOR-SERVICE",
        REPO_ROOT / "BACKEND-WEB-COLLECTOR",
        REPO_ROOT / "FRONTEND-DASHBOARD",
    ]
    for sdir in service_dirs:
        if not sdir.exists():
            continue
        # Service README
        s_readme = sdir / "README.md"
        if s_readme.exists():
            targets.append(s_readme)
        # Service docs/**
        s_docs = sdir / "docs"
        if s_docs.exists():
            for p in s_docs.rglob("*.md"):
                if p.is_file() and not is_excluded(p):
                    targets.append(p)

    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: List[Path] = []
    for p in targets:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _run(cmd: list[str]) -> Tuple[int, str, str]:
    import subprocess
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out.strip(), err.strip()


def get_head_sha() -> Optional[str]:
    code, out, _ = _run(["git", "rev-parse", "HEAD"])
    return out if code == 0 else None

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_front_matter(md: str) -> Tuple[Dict[str, str], str]:
    """Very small YAML-like parser for simple key: value lines in front-matter."""
    m = FRONT_MATTER_PATTERN.match(md)
    if not m:
        return {}, md
    header = m.group(1)
    body = md[m.end():]
    meta: Dict[str, str] = {}
    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, body


def build_front_matter(meta: Dict[str, str]) -> str:
    # Keep order stable for diffs
    lines = ["---"]
    for k in ["docsync", "last_synced", "source_sha", "coverage"]:
        if k in meta:
            lines.append(f"{k}: {meta[k]}")
    # Append any other keys
    for k in sorted(meta.keys()):
        if k not in {"docsync", "last_synced", "source_sha", "coverage"}:
            lines.append(f"{k}: {meta[k]}")
    lines.append("---\n")
    return "\n".join(lines)


def ensure_metadata(path: Path, *, head_sha: Optional[str]) -> Tuple[bool, str]:
    """Ensure front-matter exists with required keys. Returns (changed, message)."""
    content = read_text(path)
    meta, body = parse_front_matter(content)
    changed = False

    if not meta:
        meta = {
            "docsync": "true",
            "last_synced": dt.datetime.now(dt.timezone.utc).astimezone().strftime(ISO_FMT),
            "source_sha": head_sha or "",
            "coverage": "1.0",
        }
        new_content = build_front_matter(meta) + body
        write_text(path, new_content)
        return True, "initialized front-matter"

    desired = dict(meta)
    if str(desired.get("docsync", "")).lower() != "true":
        desired["docsync"] = "true"
        changed = True
    if head_sha and desired.get("source_sha") != head_sha:
        desired["source_sha"] = head_sha
        changed = True
    # Always refresh last_synced on write
    desired["last_synced"] = dt.datetime.now(dt.timezone.utc).astimezone().strftime(ISO_FMT)
    changed = True

    if changed:
        new_content = build_front_matter(desired) + body
        write_text(path, new_content)
        return True, "updated front-matter"
    return False, "no changes"


def check_docs(paths: List[Path], strict: bool = False) -> int:
    issues: list[str] = []
    warnings: list[str] = []
    for doc in paths:
        if not doc.exists():
            issues.append(f"missing doc: {doc}")
            continue
        meta, _ = parse_front_matter(read_text(doc))
        if not meta:
            issues.append(f"{doc} missing DocSync front-matter")
            continue
        if str(meta.get("docsync", "")).lower() != "true":
            issues.append(f"{doc} docsync flag != true")
        try:
            last = meta.get("last_synced")
            if last:
                try:
                    last_dt = dt.datetime.strptime(last, ISO_FMT)
                except Exception:
                    last_dt = dt.datetime.fromisoformat(last)
                age_days = (dt.datetime.now(last_dt.tzinfo) - last_dt).days
                if age_days > 30:
                    warnings.append(f"{doc} last_synced is older than 30 days")
            else:
                warnings.append(f"{doc} missing last_synced")
        except Exception as e:
            warnings.append(f"{doc} last_synced parse error: {e}")

    if issues:
        print(json.dumps({"status": "fail", "issues": issues, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1
    if warnings and strict:
        print(json.dumps({"status": "warn_strict_fail", "issues": issues, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "ok", "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0


def write_docs(paths: List[Path]) -> int:
    head_sha = get_head_sha()
    changed_any = False
    msgs: list[str] = []
    for doc in paths:
        if not doc.exists():
            # create empty file to seed metadata where appropriate
            write_text(doc, "")
        changed, msg = ensure_metadata(doc, head_sha=head_sha)
        changed_any = changed_any or changed
        msgs.append(f"{doc.relative_to(REPO_ROOT)}: {msg}")
    print(json.dumps({"status": "ok", "changed": changed_any, "messages": msgs}, ensure_ascii=False, indent=2))
    return 0


def check_required_docs(strict: bool = False) -> int:
    """Return exit code: 0 OK, 1 issues found (required doc only)."""
    return check_docs([REQUIRED_DOC], strict=strict)


def check_all_docs(strict: bool = False) -> int:
    return check_docs(get_target_docs(), strict=strict)


def write_required_docs() -> int:
    return write_docs([REQUIRED_DOC])


def write_all_docs() -> int:
    return write_docs(get_target_docs())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="DocSync CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="Verify DocSync headers and freshness")
    p_check.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    p_check.add_argument("--all", action="store_true", help="Check all repo docs")

    p_write = sub.add_parser("write", help="Initialize/update DocSync headers")
    p_write.add_argument("--all", action="store_true", help="Write headers for all repo docs")

    args = parser.parse_args(argv)

    if args.cmd == "check":
        if getattr(args, "all", False):
            return check_all_docs(strict=bool(getattr(args, "strict", False)))
        return check_required_docs(strict=bool(getattr(args, "strict", False)))
    if args.cmd == "write":
        if getattr(args, "all", False):
            return write_all_docs()
        return write_required_docs()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
