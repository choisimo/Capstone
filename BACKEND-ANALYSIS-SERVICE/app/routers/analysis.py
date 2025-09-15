from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from ..schemas import (
    ArticlesResponse,
    ChatRequest,
    ChatResponse,
    DocumentsResponse,
    GenerateReportRequest,
    GenerateReportResponse,
    MeshResponse,
    MeshMeta,
    MeshWindow,
)

router = APIRouter()


@router.get("/mesh-data", response_model=MeshResponse)
async def get_mesh_data(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    source: list[str] | None = Query(default=None),
    channel: list[str] | None = Query(default=None),
    lang: list[str] | None = Query(default=None),
    keywords: list[str] | None = Query(default=None),
    persona: list[str] | None = Query(default=None),
    emotion: list[str] | None = Query(default=None),
    experience: list[str] | None = Query(default=None),
    agg: str = Query(default="day", pattern="^(hour|day|week)$"),
    min_weight: float | None = None,
    max_nodes: int | None = None,
    scope: str = Query(default="global", pattern="^(global|article)$"),
    article_id: Optional[str] = None,
):
    now = datetime.utcnow()
    window = MeshWindow(from_=from_ or now, to=to or now, agg=agg)  # type: ignore[arg-type]
    meta = MeshMeta(window=window, filters={}, computed_at=now)
    return MeshResponse(nodes=[], links=[], meta=meta)


@router.get("/articles", response_model=ArticlesResponse)
async def list_articles(
    q: Optional[str] = None,
    source: list[str] | None = Query(default=None),
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    page: int = 1,
    size: int = 20,
    sort: str = Query(default="recency", pattern="^(recency|popularity)$"),
):
    return ArticlesResponse(total=0, items=[], agg={})


@router.get("/articles/{article_id}/mesh-data", response_model=MeshResponse)
async def get_article_mesh_data(article_id: str, min_weight: float | None = None, max_nodes: int | None = None):
    now = datetime.utcnow()
    window = MeshWindow(from_=now, to=now, agg="day")
    meta = MeshMeta(window=window, filters={"article_id": article_id}, computed_at=now)
    return MeshResponse(nodes=[], links=[], meta=meta)


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    q: Optional[str] = None,
    article_id: Optional[str] = None,
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    lang: list[str] | None = Query(default=None),
    persona: list[str] | None = Query(default=None),
    emotion: list[str] | None = Query(default=None),
    experience: list[str] | None = Query(default=None),
    keywords: list[str] | None = Query(default=None),
    page: int = 1,
    size: int = 20,
):
    return DocumentsResponse(total=0, items=[])


@router.post("/generate-report", response_model=GenerateReportResponse)
async def generate_report(req: GenerateReportRequest):
    return GenerateReportResponse(report_id="stub-1", markdown="# Report\n\nTBD", citations=[], meta={})


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return ChatResponse(reply="This is a stub reply.", sources=[], route="rag")