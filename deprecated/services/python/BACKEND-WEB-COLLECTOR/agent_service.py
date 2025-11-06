from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple, Any, Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse

# Support running as script or as package
try:
    from .config import ChangeDetectionConfig, AgentConfig, PerplexityConfig
    from .cdio_client import ChangeDetectionClient
    from .perplexity_client import PerplexityClient
except Exception:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from config import ChangeDetectionConfig, AgentConfig, PerplexityConfig  # type: ignore
    from cdio_client import ChangeDetectionClient  # type: ignore
    from perplexity_client import PerplexityClient  # type: ignore


# Allowed browser step operations from changedetection.io
ALLOWED_OPERATIONS = {
    'Choose one',
    'Check checkbox',
    'Click X,Y',
    'Click element if exists',
    'Click element',
    'Click element containing text',
    'Click element containing text if exists',
    'Enter text in field',
    'Execute JS',
    'Goto site',
    'Goto URL',
    'Make all child elements visible',
    'Press Enter',
    'Select by label',
    '<select> by option text',
    'Scroll down',
    'Uncheck checkbox',
    'Wait for seconds',
    'Wait for text',
    'Wait for text in element',
    'Remove elements',
}


class BrowserStep(BaseModel):
    operation: str = Field(..., max_length=5000)
    selector: str = Field('', max_length=5000)
    optional_value: str = Field('', max_length=5000)


class GenerateStepsRequest(BaseModel):
    url: HttpUrl
    instruction: str = Field(..., description="Natural language instructions, one step per sentence/line")


class GenerateStepsResponse(BaseModel):
    steps: List[BrowserStep]
    notes: Optional[str] = None
    warnings: Optional[List[str]] = None


class CreateWatchRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    steps: Optional[List[BrowserStep]] = None
    instruction: Optional[str] = None
    tags: Optional[List[str]] = None  # tag UUIDs
    notification_urls: Optional[List[str]] = None
    recheck: Optional[bool] = None


class CreateWatchResponse(BaseModel):
    result: str
    uuid: Optional[str] = None


class UpdateWatchRequest(BaseModel):
    steps: Optional[List[BrowserStep]] = None
    instruction: Optional[str] = None
    recheck: Optional[bool] = None


def get_clients() -> Tuple[ChangeDetectionClient, AgentConfig]:
    cdc = ChangeDetectionConfig.from_env()
    agent_cfg = AgentConfig.from_env()
    return ChangeDetectionClient(cdc.base_url, cdc.api_key), agent_cfg


def normalize_and_validate_steps(steps: List[BrowserStep], allow_execute_js: bool) -> List[BrowserStep]:
    normalized: List[BrowserStep] = []
    errors: List[str] = []
    for idx, step in enumerate(steps, start=1):
        op = (step.operation or '').strip()
        if op not in ALLOWED_OPERATIONS:
            errors.append(f"Step {idx}: Unsupported operation '{op}'")
            continue
        if op == 'Execute JS' and not allow_execute_js:
            errors.append(f"Step {idx}: 'Execute JS' not permitted by configuration")
            continue
        sel = (step.selector or '')
        val = (step.optional_value or '')
        normalized.append(BrowserStep(operation=op, selector=sel, optional_value=val))

    if errors:
        raise HTTPException(status_code=400, detail={"message": "Invalid steps", "errors": errors})

    return normalized


# Very simple rule-based parser as a fallback when no LLM provider is configured
CLICK_TEXT_RE = re.compile(r"click (?:element )?(?:containing text|text) ['\"](.+?)['\"]", re.IGNORECASE)
CLICK_SELECTOR_RE = re.compile(r"click (?:element )?([#\./][^\s]+|//[^\s]+|xpath=[^\s]+)", re.IGNORECASE)
TYPE_INTO_RE = re.compile(r"(?:type|enter) ['\"](.+?)['\"] (?:into|in) (.+)", re.IGNORECASE)
WAIT_SECONDS_RE = re.compile(r"wait (\d+(?:\.\d+)?) seconds?", re.IGNORECASE)
GOTO_URL_RE = re.compile(r"(?:go to|goto|open) (?:url )?['\"](https?://[^'\"]+)['\"]", re.IGNORECASE)
SELECT_BY_LABEL_RE = re.compile(r"select ['\"](.+?)['\"] (?:in|from) (.+)", re.IGNORECASE)
PRESS_ENTER_RE = re.compile(r"press enter", re.IGNORECASE)
SCROLL_DOWN_RE = re.compile(r"scroll down", re.IGNORECASE)


def naive_generate_steps(url: str, instruction: str) -> List[BrowserStep]:
    steps: List[BrowserStep] = [BrowserStep(operation='Goto URL', selector='', optional_value=url)]

    # Split instructions into lines/sentences
    parts = re.split(r"[\n\r]+|\.\s+", instruction)
    for raw in parts:
        line = raw.strip()
        if not line:
            continue

        m = GOTO_URL_RE.search(line)
        if m:
            steps.append(BrowserStep(operation='Goto URL', selector='', optional_value=m.group(1)))
            continue

        m = CLICK_TEXT_RE.search(line)
        if m:
            steps.append(BrowserStep(operation='Click element containing text', selector='', optional_value=m.group(1)))
            continue

        m = CLICK_SELECTOR_RE.search(line)
        if m:
            steps.append(BrowserStep(operation='Click element', selector=m.group(1), optional_value=''))
            continue

        m = TYPE_INTO_RE.search(line)
        if m:
            value, selector = m.group(1), m.group(2).strip()
            steps.append(BrowserStep(operation='Enter text in field', selector=selector, optional_value=value))
            continue

        m = WAIT_SECONDS_RE.search(line)
        if m:
            steps.append(BrowserStep(operation='Wait for seconds', selector='', optional_value=m.group(1)))
            continue

        m = SELECT_BY_LABEL_RE.search(line)
        if m:
            label, selector = m.group(1), m.group(2).strip()
            steps.append(BrowserStep(operation='Select by label', selector=selector, optional_value=label))
            continue

        if PRESS_ENTER_RE.search(line):
            steps.append(BrowserStep(operation='Press Enter', selector='', optional_value=''))
            continue

        if SCROLL_DOWN_RE.search(line):
            steps.append(BrowserStep(operation='Scroll down', selector='', optional_value=''))
            continue

        # Unknown instruction -> ignore silently

    return steps


app = FastAPI(title="AI Agent for ChangeDetection.io", version="0.1.0")

# Enable CORS for the React dev server and others
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", response_class=HTMLResponse)
def root():
    return "<h3>AI Agent for ChangeDetection.io</h3><p>See /docs for API, frontend connects to this server.</p>"


@app.post("/api/v1/agent/generate-steps", response_model=GenerateStepsResponse)
def generate_steps(req: GenerateStepsRequest):
    _, agent_cfg = get_clients()

    # Currently only the naive rule-based generator is implemented
    steps = naive_generate_steps(str(req.url), req.instruction)
    steps = normalize_and_validate_steps(steps, allow_execute_js=agent_cfg.allow_execute_js)

    notes = (
        "Generated with rule-based parser. Improve by configuring an LLM provider."
    )
    return GenerateStepsResponse(steps=steps, notes=notes)


@app.post("/api/v1/agent/create-watch", response_model=CreateWatchResponse)
def create_watch(req: CreateWatchRequest):
    client, agent_cfg = get_clients()

    if req.steps is None and (req.instruction is None or not req.instruction.strip()):
        raise HTTPException(status_code=400, detail="Provide either 'steps' or 'instruction'.")

    # Build steps
    if req.steps is None:
        steps = naive_generate_steps(str(req.url), req.instruction or "")
    else:
        steps = req.steps

    steps = normalize_and_validate_steps(steps, allow_execute_js=agent_cfg.allow_execute_js)

    payload: Dict[str, Any] = {
        "url": str(req.url),
        "fetch_backend": "html_webdriver",
        "browser_steps": [s.dict() for s in steps],
    }
    if req.title:
        payload["title"] = req.title
    if req.tags:
        payload["tags"] = req.tags
    if req.notification_urls:
        payload["notification_urls"] = req.notification_urls

    result = client.create_watch(payload)

    # Attempt to discover the newly created UUID via search
    discovered_uuid: Optional[str] = None
    try:
        search = client.search(q=str(req.url), partial=False)
        watches = (search or {}).get("watches", {})
        for uuid, w in watches.items():
            if str(w.get("url", "")).strip().rstrip('/') == str(req.url).strip().rstrip('/'):
                discovered_uuid = uuid
                break
    except Exception:
        pass

    # Optional recheck
    recheck_flag = req.recheck if req.recheck is not None else agent_cfg.default_recheck_on_create
    if discovered_uuid and recheck_flag:
        try:
            client.get_watch(discovered_uuid, recheck=True)
        except Exception:
            pass

    return CreateWatchResponse(result=result, uuid=discovered_uuid)


@app.put("/api/v1/agent/update-watch/{uuid}")
def update_watch(uuid: str, req: UpdateWatchRequest):
    client, agent_cfg = get_clients()

    if req.steps is None and (req.instruction is None or not req.instruction.strip()):
        raise HTTPException(status_code=400, detail="Provide either 'steps' or 'instruction'.")

    # Load full watch JSON, then update fields as needed (PUT expects full structure)
    try:
        watch = client.get_watch(uuid)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Watch not found: {e}")

    if req.steps is None:
        url = watch.get("url") or ""
        steps = naive_generate_steps(str(url), req.instruction or "")
    else:
        steps = req.steps

    steps = normalize_and_validate_steps(steps, allow_execute_js=agent_cfg.allow_execute_js)

    watch["fetch_backend"] = "html_webdriver"
    watch["browser_steps"] = [s.dict() for s in steps]

    result = client.update_watch(uuid, watch)

    # Optional recheck
    recheck_flag = req.recheck if req.recheck is not None else agent_cfg.default_recheck_on_update
    if recheck_flag:
        try:
            client.get_watch(uuid, recheck=True)
        except Exception:
            pass

    return {"result": result}


# ---- UI helper endpoints for React frontend ----
@app.get("/api/v1/ui/agent-info")
def ui_agent_info():
    cdc = ChangeDetectionConfig.from_env()
    agent = AgentConfig.from_env()
    return {
        "cd_base_url": cdc.base_url,
        "api_key_configured": bool(cdc.api_key),
        "agent": {
            "port": agent.port,
            "allow_execute_js": agent.allow_execute_js,
            "default_recheck_on_create": agent.default_recheck_on_create,
            "default_recheck_on_update": agent.default_recheck_on_update,
        },
    }


@app.get("/api/v1/ui/watches")
def ui_list_watches(tag: Optional[str] = Query(default=None)):
    client, _ = get_clients()
    return client.list_watches(tag=tag)


@app.get("/api/v1/ui/systeminfo")
def ui_systeminfo():
    client, _ = get_clients()
    try:
        return client.systeminfo()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/v1/ui/tags")
def ui_tags():
    client, _ = get_clients()
    return client.list_tags()


@app.get("/api/v1/ui/search")
def ui_search(q: str, partial: bool = False, tag: Optional[str] = None):
    client, _ = get_clients()
    return client.search(q=q, partial=partial, tag=tag)


@app.get("/api/v1/ui/watch/{uuid}")
def ui_get_watch(uuid: str):
    client, _ = get_clients()
    res = client.get_watch(uuid)
    if isinstance(res, dict):
        return res
    return {"result": res}


@app.delete("/api/v1/ui/watch/{uuid}")
def ui_delete_watch(uuid: str):
    client, _ = get_clients()
    res = client.delete_watch(uuid)
    return {"result": res}


@app.post("/api/v1/ui/recheck/{uuid}")
def ui_recheck(uuid: str):
    client, _ = get_clients()
    res = client.get_watch(uuid, recheck=True)
    if isinstance(res, dict):
        return {"result": "OK"}
    return {"result": res}


@app.get("/api/v1/ui/snapshot/{uuid}")
def ui_snapshot(uuid: str, timestamp: str = "latest", html: bool = False):
    client, _ = get_clients()
    text = client.get_snapshot(uuid, timestamp, html=html)
    if html:
        return HTMLResponse(text)
    return PlainTextResponse(text)


@app.post("/api/v1/ui/import")
def ui_import(urls: str = Query(..., description="Line separated URLs"), tag: Optional[str] = None):
    client, _ = get_clients()
    try:
        return client.import_urls(text=urls, tag=tag)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/agent/search")
def agent_search(
    q: str = Query(..., description="Search query"),
    engine: str = Query("cd", pattern=r"^(cd|pplx)$", description="Search engine: 'cd' (changedetection) or 'pplx' (Perplexity)"),
    top_k: int = Query(10, ge=1, le=50),
    partial: bool = Query(False, description="Partial match for changedetection search"),
    tag: Optional[str] = Query(None, description="Tag filter for changedetection"),
):
    """
    Unified search endpoint.

    - engine=cd: Use changedetection.io watch search.
    - engine=pplx: Use Perplexity AI API (requires PPLX_API_KEY configured).

    Returns normalized list under key 'results'.
    """
    results: List[Dict[str, Any]] = []
    chosen_engine = engine

    if engine == "pplx":
        cfg = PerplexityConfig.from_env()
        if not cfg.api_key:
            # Fallback to changedetection if Perplexity is not configured
            chosen_engine = "cd"
        else:
            try:
                pplx = PerplexityClient(cfg.base_url, cfg.api_key, model=cfg.model, timeout=cfg.timeout_sec)
                results = pplx.search(q=q, top_k=top_k)
                return {"engine": "pplx", "results": results}
            except Exception as e:
                # Fallback to cd on error as well
                chosen_engine = "cd"
                fallback_reason = str(e)
    else:
        fallback_reason = None

    # changedetection fallback or primary path
    client, _ = get_clients()
    try:
        cd_res = client.search(q=q, partial=partial, tag=tag)
        watches = (cd_res or {}).get("watches", {})
        for uuid, w in (watches or {}).items():
            if not isinstance(w, dict):
                continue
            results.append({
                "title": str(w.get("title") or ""),
                "url": str(w.get("url") or ""),
                "snippet": "",
                "score": 1.0,
                "source": "changedetection",
                "uuid": uuid,
            })
        payload: Dict[str, Any] = {"engine": "cd", "results": results}
        if engine == "pplx":
            payload["warning"] = "Perplexity not available, fell back to changedetection."
            if fallback_reason:
                payload["reason"] = fallback_reason
        return payload
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search failed: {e}")


if __name__ == "__main__":
    import uvicorn

    cfg = AgentConfig.from_env()
    uvicorn.run(app, host="0.0.0.0", port=cfg.port, reload=os.getenv("UVICORN_RELOAD", "0") in ("1", "true", "True"))
