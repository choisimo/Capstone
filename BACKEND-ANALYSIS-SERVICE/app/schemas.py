from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# Mesh graph
class MeshNode(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    weight: Optional[float] = None


class MeshLink(BaseModel):
    source: str
    target: str
    weight: Optional[float] = None
    pmi: Optional[float] = None


class MeshWindow(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime
    agg: Literal["hour", "day", "week"]

    class Config:
        populate_by_name = True


class MeshMeta(BaseModel):
    window: MeshWindow
    filters: Dict[str, Any] = {}
    computed_at: datetime


class MeshResponse(BaseModel):
    nodes: List[MeshNode]
    links: List[MeshLink]
    meta: MeshMeta


# Articles
class Article(BaseModel):
    id: str
    title: str
    url: str
    published_at: datetime
    source: str
    keywords: List[str] = []


class ArticlesAgg(BaseModel):
    by_source: List[Dict[str, Any]] = []
    by_time: List[Dict[str, Any]] = []


class ArticlesResponse(BaseModel):
    total: int
    items: List[Article]
    agg: ArticlesAgg = ArticlesAgg()


# Documents
class DocumentMeta(BaseModel):
    sentiment: Optional[str] = None
    persona: List[str] = []
    experience: List[str] = []
    keywords: List[str] = []
    lang: Optional[str] = None


class Document(BaseModel):
    id: str
    ts: datetime
    source: str
    channel: str
    article_id: Optional[str] = None
    text: str
    meta: DocumentMeta = DocumentMeta()


class DocumentsResponse(BaseModel):
    total: int
    items: List[Document]


# Report generation
class NodeRef(BaseModel):
    type: str
    id: Optional[str] = None
    label: Optional[str] = None


class ReportOptions(BaseModel):
    style: Optional[str] = None
    length: Optional[str] = None
    audience: Optional[str] = None


class GenerateReportRequest(BaseModel):
    nodes: List[NodeRef]
    template: Optional[str] = None
    options: Optional[ReportOptions] = None


class Citation(BaseModel):
    doc_id: str
    span: Optional[str] = None


class GenerateReportResponse(BaseModel):
    report_id: str
    markdown: str
    citations: List[Citation] = []
    meta: Dict[str, Any] = {}


# Chat
class ChatContext(BaseModel):
    nodes: Optional[List[NodeRef]] = None
    filters: Optional[Dict[str, Any]] = None
    k: Optional[int] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []
    route: Literal["rag", "summary", "search"] = "rag"