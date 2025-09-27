#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_docs.py

Recursively cleans documentation files by:
- Removing emoji/pictograph icons (outside code blocks)
- Normalizing markdown heading spacing (e.g., "###   제목" -> "### 제목")
- Removing trailing whitespace (outside code blocks)

Safeguards:
- Skips common vendor/third-party directories
- Only processes selected extensions: .md, .markdown, .rst, .txt
- Preserves content in fenced code blocks (``` or ~~~)

Usage:
  python scripts/cleanup_docs.py --root . --dry-run
  python scripts/cleanup_docs.py --root .

Options:
  --root <path>        Root directory to scan (default: repository root inferred from this script)
  --dry-run            Do not write changes; only show summary
  --verbose            Print per-file details
  --update-revision    Append a simple revision row if a "개정 이력" table exists (safe best-effort)

"""

from __future__ import annotations
import argparse
import os
import re
import sys
from datetime import datetime
from typing import Iterable, List, Tuple

# Target file extensions
DOC_EXTS = {".md", ".markdown", ".rst", ".txt"}

# Excluded directory names (skip if any path component matches)
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv", ".venv",
    "env", ".env",
    "dist", "build", ".next",
    "site-packages",
    "__pycache__",
    ".cursor",
    ".windsurf",
    "deepwiki-env",
    # project-specific vendor/embedded third-party
    "changedetectionio",
}

# Precompiled regex for emoji/pictograph ranges commonly used for decorative icons
# Note: We avoid CJK ranges to not break Korean/Chinese text.
EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FAFF"
    r"\u2600-\u26FF\u2700-\u27BF\uFE0F\u200D]",
    flags=re.UNICODE,
)

# Fenced code block delimiters
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Markdown heading marker at line start
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})(?P<space>\s*)")

# Table detection for revision updates
REVISION_HEADER_RE = re.compile(r"^##\s*개정\s*이력\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\|\s*-+")


def should_exclude_dir(path_parts: Iterable[str]) -> bool:
    for part in path_parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def iter_doc_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place for efficiency
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        if should_exclude_dir(os.path.relpath(dirpath, root).split(os.sep)):
            continue
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in DOC_EXTS:
                yield os.path.join(dirpath, fn)


def clean_lines(lines: List[str]) -> Tuple[List[str], bool]:
    """Return cleaned lines and whether any change was made."""
    changed = False
    in_code = False
    cleaned: List[str] = []

    for line in lines:
        line_out = line
        fence_match = FENCE_RE.match(line)
        if fence_match:
            # Toggle code block state; keep fences as-is
            # If a line both opens and closes a fence on the same line (e.g., "```inline```"),
            # do not toggle state (treat it as a literal line to preserve content safely).
            fence_token = fence_match.group(1)
            rest = line[fence_match.end():]
            if fence_token in rest:
                cleaned.append(line_out)
                continue
            in_code = not in_code
            cleaned.append(line_out)
            continue

        if not in_code:
            # Remove emojis/pictographs
            new_line = EMOJI_RE.sub("", line_out)

            # Normalize markdown heading spacing: ensure single space after ###
            m = HEADING_RE.match(new_line)
            if m:
                hashes = m.group("hashes")
                rest = new_line[m.end():]
                # Avoid touching setext style headings (underlines) - not applicable here
                new_line = f"{hashes} {rest.lstrip()}"

            # Remove trailing whitespace
            new_line = re.sub(r"[ \t]+$", "", new_line)

            if new_line != line_out:
                changed = True
            line_out = new_line
        else:
            # inside code block: keep as-is
            pass

        cleaned.append(line_out)

    return cleaned, changed


def maybe_update_revision(lines: List[str]) -> Tuple[List[str], bool]:
    """If a '## 개정 이력' markdown table exists, append a row for today's cleanup.
    Conservative: requires a table header and separator already present.
    """
    try:
        idx = next(i for i, l in enumerate(lines) if REVISION_HEADER_RE.match(l.strip()))
    except StopIteration:
        return lines, False

    # Look for table header starting after idx
    table_start = None
    for j in range(idx + 1, min(idx + 10, len(lines))):
        if lines[j].strip().startswith("|"):
            table_start = j
            break
    if table_start is None:
        return lines, False

    # Ensure next line is a separator row like |---|---|
    if table_start + 1 >= len(lines) or not TABLE_SEPARATOR_RE.match(lines[table_start + 1].strip()):
        return lines, False

    today = datetime.now().strftime("%Y-%m-%d")
    new_row = f"| {today} | auto | 문서 간소화 및 아이콘 제거 | 스크립트 |\n"

    # Insert row after header and separator (at table_start + 2), but keep newest on top if already sorted
    insert_pos = table_start + 2
    # If there is an existing row for today, skip
    for k in range(insert_pos, min(insert_pos + 10, len(lines))):
        if lines[k].startswith(f"| {today} "):
            return lines, False

    lines = lines[:insert_pos] + [new_row] + lines[insert_pos:]
    return lines, True


def process_file(path: str, dry_run: bool, verbose: bool, update_revision: bool) -> Tuple[bool, int]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        orig = f.readlines()

    cleaned, changed = clean_lines(orig)

    rev_changed = False
    if update_revision and changed:
        cleaned, rev_changed = maybe_update_revision(cleaned)
        changed = changed or rev_changed

    if changed and not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(cleaned)

    if verbose and changed:
        print(f"✔ Updated: {path}")
    return changed, len(orig)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Cleanup documentation files across the repo")
    parser.add_argument("--root", default=None, help="Root directory (default: repo root)")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would change")
    parser.add_argument("--verbose", action="store_true", help="Print per-file updates")
    parser.add_argument("--update-revision", action="store_true", help="Append a row to existing '개정 이력' table if present")
    args = parser.parse_args(argv)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..")) if not args.root else os.path.abspath(args.root)

    total_files = 0
    changed_files = 0

    for fp in iter_doc_files(repo_root):
        total_files += 1
        changed, _ = process_file(fp, dry_run=args.dry_run, verbose=args.verbose, update_revision=args.update_revision)
        if changed:
            changed_files += 1

    print("---")
    print(f"Scanned files: {total_files}")
    print(f"Changed files: {changed_files}{' (dry-run)' if args.dry_run else ''}")
    if args.dry_run:
        print("Run without --dry-run to apply changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
