#!/usr/bin/env python3
"""Generate markdown manifest (JSON) and MkDocs nav YAML."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_OUTPUT_PATH = REPO_ROOT / "docs" / "wiki" / "data" / "docs.json"

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "mkdocs",
    "venv",
    "env",
    ".venv",
    "build",
    "dist",
    "out",
    "coverage",
    "tmp",
    "temp",
    "logs",
    ".idea",
    ".vscode",
    "vendor",
}


def find_markdown_files(root: Path) -> List[str]:
    """Return sorted list of markdown paths relative to repo root."""

    files: List[str] = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        files.append(relative)
    return sorted(files)


def _format_title(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().title() or name


def build_nav_structure(files: Iterable[str]) -> List[Dict[str, object]]:
    """Convert file paths into MkDocs nav structure."""

    tree: Dict[str, Dict[str, object]] = {"_files": []}

    for path in files:
        parts = path.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {"_files": []})  # type: ignore[assignment]
        node.setdefault("_files", []).append(path)  # type: ignore[assignment]

    def finalize(node: Dict[str, object]) -> List[Dict[str, object]]:
        items: List[Dict[str, object]] = []
        for key in sorted(k for k in node.keys() if k != "_files"):
            child = node[key]  # type: ignore[index]
            items.append({_format_title(key): finalize(child)})
        for file_path in sorted(node.get("_files", [])):  # type: ignore[assignment]
            title = _format_title(Path(file_path).stem)
            items.append({title: file_path})
        return items

    return finalize(tree)


def write_json_manifest(files: List[str]) -> None:
    entries = [
        {
            "path": path,
            "title": _format_title(Path(path).stem),
        }
        for path in files
    ]

    JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "files": entries,
    }
    JSON_OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"✅ JSON manifest created at {JSON_OUTPUT_PATH}")


def emit_nav_yaml(files: List[str]) -> None:
    if yaml is None:
        print("PyYAML is required for YAML output. Install with 'pip install pyyaml'.", file=sys.stderr)
        sys.exit(1)

    nav_structure = build_nav_structure(files)
    header = (
        "# This is an auto-generated navigation structure for mkdocs.yml.\n"
        "# Run 'python scripts/generate_wiki_manifest.py --format yaml' to regenerate."
    )
    print(header)
    yaml.dump(nav_structure, sys.stdout, allow_unicode=True, sort_keys=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate markdown manifest (JSON) or MkDocs navigation YAML.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (json writes to docs/wiki/data/docs.json, yaml prints nav to stdout)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown_files = find_markdown_files(REPO_ROOT)

    if args.format == "json":
        write_json_manifest(markdown_files)
    else:
        emit_nav_yaml(markdown_files)


if __name__ == "__main__":
    main()
