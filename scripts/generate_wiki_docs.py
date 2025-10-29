#!/usr/bin/env python3
from __future__ import annotations

"""Generate static wiki docs bundle for GitHub Pages."""

import argparse
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "wiki-docs-build"
SITE_SUBDIR = "wiki-docs"
RAW_SUBDIR = "raw"

EXCLUDED_DIR_NAMES = {".git", "node_modules", "__pycache__", "venv", ".venv", "env", ".mypy_cache", ".pytest_cache"}
DOC_EXTS = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".html", ".htm", ".pdf", ".doc", ".docx", ".json", ".yaml", ".yml", ".csv", ".tsv", ".log"}
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp", ".ico", ".css", ".js", ".xml", ".ini", ".conf", ".ttf", ".woff", ".woff2"}
ALLOWED_EXTS = DOC_EXTS | ASSET_EXTS
TEXTUAL_PREVIEW_EXTS = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".json", ".yaml", ".yml", ".csv", ".tsv", ".log"}
BASE_DOC_DIRS = [REPO_ROOT / "docs", REPO_ROOT / "DOCUMENTS", REPO_ROOT / ".windsurf/workflows"]
README_GLOBS = ["README.md", "README-*.md", "**/README.md", "**/README-*.md"]

INDEX_HTML = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n  <title>Wiki Docs Index</title>\n  <style>body{margin:0;padding:0 1.5rem 2rem;font-family:system-ui;color:#0f172a;background:#f8fafc;}table{width:100%;border-collapse:collapse;font-size:.94rem;}thead{background:rgba(15,23,42,.08);}th,td{padding:.6rem .5rem;border-bottom:1px solid rgba(15,23,42,.1);}tbody tr:hover{background:rgba(59,130,246,.1);}header{padding:1.5rem 0 1rem;}h1{margin:0 0 .5rem;font-size:clamp(1.6rem,2vw+1rem,2.2rem);}p.lead{margin:0 0 1.4rem;color:#475569;}input[type=search]{width:min(420px,100%);padding:.55rem .75rem;border-radius:8px;border:1px solid rgba(148,163,184,.6);}a{color:#2563eb;text-decoration:none;}a:hover{text-decoration:underline;}td.path{word-break:break-all;font-family:ui-monospace;}footer{margin-top:2rem;font-size:.82rem;color:#64748b;}</style>\n</head>\n<body>\n  <header>\n    <h1>Wiki Documentation Portal</h1>\n    <p class=\"lead\">Repository 문서를 한곳에서 검색하고 열람합니다.</p>\n    <input type=\"search\" id=\"filter\" placeholder=\"문서 경로 검색...\" />\n    <div class=\"stats\" id=\"stats\"></div>\n  </header>\n  <table>\n    <thead><tr><th>문서 경로</th><th>형식</th><th>크기</th></tr></thead>\n    <tbody id=\"docs-body\"></tbody>\n  </table>\n  <footer>docs-data.json 기준으로 최신 문서를 제공합니다.</footer>\n<script>async function loadDocs(){const r=await fetch('docs-data.json',{cache:'no-store'});if(!r.ok)throw new Error('문서 데이터를 불러올 수 없습니다.');return (await r.json()).files||[];}function fmt(b){if(!b)return'0 B';const u=['B','KB','MB','GB'],i=Math.floor(Math.log(b)/Math.log(1024));const v=b/Math.pow(1024,i);return`${v.toFixed(v<10&&i>0?1:0)} ${u[i]}`;}function render(fs){const b=document.getElementById('docs-body');b.innerHTML='';fs.forEach(f=>{const tr=document.createElement('tr');const tdPath=document.createElement('td');tdPath.className='path';const link=document.createElement('a');link.href=`viewer.html?path=${encodeURIComponent(f.path)}`;link.textContent=f.path;tdPath.appendChild(link);tr.appendChild(tdPath);const tdExt=document.createElement('td');tdExt.textContent=f.ext.toUpperCase();tr.appendChild(tdExt);const tdSize=document.createElement('td');tdSize.textContent=fmt(f.size);tr.appendChild(tdSize);b.appendChild(tr);});document.getElementById('stats').textContent=`${fs.length.toLocaleString()}개 문서`; }function setup(fs){const input=document.getElementById('filter');input.addEventListener('input',()=>{const v=input.value.trim().toLowerCase();if(!v)return render(fs);render(fs.filter(f=>f.path.toLowerCase().includes(v)));});}loadDocs().then(fs=>{const sorted=fs.slice().sort((a,b)=>a.path.localeCompare(b.path));render(sorted);setup(sorted);}).catch(err=>{document.getElementById('docs-body').innerHTML=`<tr><td colspan=\"3\">${err.message}</td></tr>`;});</script>\n</body>\n</html>\n"

VIEWER_HTML = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n  <title>문서 뷰어</title>\n  <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>\n  <style>body{margin:0;background:#e2e8f0;font-family:system-ui;}header{position:sticky;top:0;display:flex;justify-content:space-between;align-items:center;padding:1rem 1.5rem;background:rgba(255,255,255,.9);border-bottom:1px solid rgba(148,163,184,.5);backdrop-filter:blur(8px);}h1{margin:0;font-size:1rem;word-break:break-all;font-family:ui-monospace;}main{max-width:1200px;margin:0 auto;padding:1.5rem;}#content{background:#fff;border-radius:12px;box-shadow:0 10px 35px rgba(15,23,42,.07);padding:1.5rem;min-height:70vh;overflow-x:auto;}a.button{display:inline-flex;align-items:center;padding:.45rem .85rem;border-radius:7px;text-decoration:none;font-size:.85rem;}a.primary{background:#2563eb;color:#fff;}a.secondary{background:rgba(148,163,184,.3);color:#1f2937;margin-right:.6rem;}pre{background:rgba(15,23,42,.08);padding:1rem;border-radius:10px;overflow:auto;}iframe.preview{width:100%;min-height:70vh;border:1px solid rgba(148,163,184,.4);border-radius:10px;background:#fff;}</style>\n</head>\n<body>\n  <header>\n    <h1 id=\"doc-path\">문서 로드 중...</h1>\n    <nav>\n      <a class=\"button secondary\" href=\"index.html\">← 목록</a>\n      <a class=\"button primary\" id=\"raw-link\" target=\"_blank\">Raw</a>\n    </nav>\n  </header>\n  <main>\n    <section id=\"content\">문서를 불러오는 중입니다...</section>\n  </main>\n<script>function qp(n){return new URLSearchParams(window.location.search).get(n);}function ext(p){const i=p.lastIndexOf('.');return i===-1?'':p.slice(i).toLowerCase();}async function load(){const path=qp('path');if(!path){document.getElementById('content').textContent='path 파라미터가 필요합니다.';return;}document.title=path+' – 문서 뷰어';document.getElementById('doc-path').textContent=path;const raw=`raw/${path}`;document.getElementById('raw-link').href=raw;const extension=ext(path);if(['.pdf','.doc','.docx'].includes(extension)){document.getElementById('content').innerHTML='<p>브라우저 미리보기를 지원하지 않는 형식입니다. Raw 링크를 통해 다운로드하세요.</p>';return;}if(['.html','.htm'].includes(extension)){document.getElementById('content').innerHTML=`<iframe class=\"preview\" src='${raw}'></iframe>`;return;}try{const res=await fetch(raw,{cache:'no-store'});if(!res.ok)throw new Error('문서 요청 실패');const text=await res.text();if(['.md','.markdown','.mdx'].includes(extension)){document.getElementById('content').innerHTML=marked.parse(text,{mangle:false,headerIds:true});return;}if(['.json','.yaml','.yml','.csv','.tsv','.txt','.rst','.adoc','.log'].includes(extension)){const escaped=text.replace(/[&<>]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[ch]));document.getElementById('content').innerHTML=`<pre>${escaped}</pre>`;return;}document.getElementById('content').innerHTML='<p>이 형식은 기본 미리보기 대상이 아닙니다. Raw 링크를 통해 확인하세요.</p>'; }catch(err){document.getElementById('content').textContent=`문서를 불러오지 못했습니다: ${err.message}`;}}load();</script>\n</body>\n</html>\n"

ROOT_REDIRECT_HTML = "<!DOCTYPE html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\" /><meta http-equiv=\"refresh\" content=\"0;url=wiki-docs/index.html\" /><title>Redirecting…</title></head>\n<body><p><a href=\"wiki-docs/index.html\">wiki-docs/index.html</a>로 이동합니다.</p></body>\n</html>\n"


def should_exclude(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def discover_doc_dirs(root: Path) -> List[Path]:
    doc_dirs = {p for p in BASE_DOC_DIRS if p.exists()}
    for dirpath, dirnames, _ in os.walk(root):
        current = Path(dirpath)
        if should_exclude(current):
            dirnames[:] = []
            continue
        for name in list(dirnames):
            if name in EXCLUDED_DIR_NAMES:
                dirnames.remove(name)
        for name in dirnames:
            if name.lower() == "docs":
                doc_dirs.add(current / name)
    return sorted(doc_dirs)


def collect_doc_files(root: Path, doc_dirs: Sequence[Path]) -> List[Path]:
    files = set()
    for directory in doc_dirs:
        for file in directory.rglob("*"):
            if file.is_file() and not should_exclude(file) and (not file.suffix or file.suffix.lower() in ALLOWED_EXTS):
                files.add(file)
    for pattern in README_GLOBS:
        for file in root.glob(pattern):
            if file.is_file() and not should_exclude(file) and (not file.suffix or file.suffix.lower() in ALLOWED_EXTS):
                files.add(file)
    for child in root.iterdir():
        if child.is_dir() and not should_exclude(child):
            for file in child.glob("*.md"):
                if file.is_file():
                    files.add(file)
    return sorted(files)


def is_textual(file: Path) -> bool:
    return file.suffix.lower() in TEXTUAL_PREVIEW_EXTS or file.suffix.lower() in {".md", ".markdown", ".mdx"}


def build_docs_payload(files: Iterable[Path]) -> List[dict]:
    payload = []
    for file in files:
        rel = file.relative_to(REPO_ROOT).as_posix()
        payload.append({"path": rel, "ext": file.suffix.lower()[1:] if file.suffix else "", "size": file.stat().st_size, "textual": is_textual(file)})
    return sorted(payload, key=lambda item: item["path"])


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_doc_assets(doc_dirs: Sequence[Path], output_raw: Path) -> None:
    for directory in doc_dirs:
        for file in directory.rglob("*"):
            if file.is_file() and not should_exclude(file):
                if file.suffix and file.suffix.lower() not in ALLOWED_EXTS:
                    continue
                rel = file.relative_to(REPO_ROOT)
                copy_file(file, output_raw / rel)


def copy_doc_files(files: Sequence[Path], output_raw: Path) -> None:
    for file in files:
        rel = file.relative_to(REPO_ROOT)
        copy_file(file, output_raw / rel)


def write_site_assets(site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (site_dir / "viewer.html").write_text(VIEWER_HTML, encoding="utf-8")


def write_docs_data(site_dir: Path, files: Sequence[dict]) -> None:
    payload = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "files": files}
    (site_dir / "docs-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_root_redirect(output_dir: Path) -> None:
    (output_dir / "index.html").write_text(ROOT_REDIRECT_HTML, encoding="utf-8")


def clean_output(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def generate(output_dir: Path, include_assets: bool = True) -> int:
    doc_dirs = discover_doc_dirs(REPO_ROOT)
    doc_files = collect_doc_files(REPO_ROOT, doc_dirs)
    if not doc_files:
        print("No documentation files discovered.")
        return 1
    clean_output(output_dir)
    site_dir = output_dir / SITE_SUBDIR
    raw_dir = site_dir / RAW_SUBDIR
    write_site_assets(site_dir)
    copy_doc_files(doc_files, raw_dir)
    if include_assets:
        copy_doc_assets(doc_dirs, raw_dir)
    docs_payload = build_docs_payload(doc_files)
    write_docs_data(site_dir, docs_payload)
    write_root_redirect(output_dir)
    print(f"Generated {len(docs_payload)} docs into {output_dir}")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate wiki docs bundle")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Build output directory (default: repo/wiki-docs-build)")
    parser.add_argument("--no-assets", action="store_true", help="Skip copying additional assets")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return generate(args.output, include_assets=not args.no_assets)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
