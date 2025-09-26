from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class DataSourceCreate(BaseModel):
    name: str
    url: str
    source_type: str
    collection_frequency: int = 3600
    metadata_json: Optional[dict] = None

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    collection_frequency: Optional[int] = None
    metadata_json: Optional[dict] = None

class DataSource(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    is_active: bool
    last_collected: Optional[datetime] = None
    collection_frequency: int
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CollectedDataCreate(BaseModel):
    source_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    metadata_json: Optional[dict] = None

class CollectedData(BaseModel):
    id: int
    source_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    collected_at: datetime
    content_hash: Optional[str] = None
    metadata_json: Optional[dict] = None
    processed: bool = False
    # QA pipeline results
    http_ok: Optional[bool] = None
    has_content: Optional[bool] = None
    duplicate: Optional[bool] = None
    normalized: Optional[bool] = None
    quality_score: Optional[float] = None
    semantic_consistency: Optional[float] = None
    outlier_score: Optional[float] = None
    trust_score: Optional[float] = None

    class Config:
        from_attributes = True

class CollectionJobCreate(BaseModel):
    source_id: int

class CollectionJob(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_collected: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CollectionStats(BaseModel):
    total_sources: int
    active_sources: int
    total_items_collected: int
    items_collected_today: int
    last_collection: Optional[datetime] = None

class CollectionRequest(BaseModel):
    source_ids: Optional[List[int]] = None
    force: bool = False

class RSSFeedItem(BaseModel):
    title: str
    description: str
    link: str
    published_date: datetime
    guid: Optional[str] = None

class ScrapedContent(BaseModel):
    title: str
    content: str
    url: str
    metadata: Optional[dict] = None