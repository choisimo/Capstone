from typing import Optional, List, Dict
from datetime import datetime

class SourceCategoryEnum:
    news = "news"
    social_media = "social_media"
    blog = "blog"
    forum = "forum"
    government = "government"
    corporate = "corporate"
    academic = "academic"
    other = "other"

class SourceStatusEnum:
    active = "active"
    inactive = "inactive"
    blocked = "blocked"
    pending = "pending"

class SourceBase:
    def __init__(self, url: str, category: str = SourceCategoryEnum.other, 
                 region: str = "KR", metadata: Optional[Dict] = None):
        self.url = url
        self.category = category
        self.region = region
        self.metadata = metadata or {}

class SourceCreate(SourceBase):
    def __init__(self, url: str, category: str = SourceCategoryEnum.other, 
                 region: str = "KR", metadata: Optional[Dict] = None):
        super().__init__(url, category, region, metadata)

class SourceUpdate:
    def __init__(self, category: Optional[str] = None, region: Optional[str] = None,
                 trust_score: Optional[float] = None, status: Optional[str] = None,
                 crawl_policy: Optional[Dict] = None, metadata: Optional[Dict] = None):
        self.category = category
        self.region = region
        self.trust_score = trust_score
        self.status = status
        self.crawl_policy = crawl_policy
        self.metadata = metadata

class SourceResponse(SourceBase):
    def __init__(self, id: int, url: str, host: str, category: str, region: str,
                 trust_score: float, status: str, last_crawl_at: Optional[datetime] = None,
                 failure_count: int = 0, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, metadata: Optional[Dict] = None):
        super().__init__(url, category, region, metadata)
        self.id = id
        self.host = host
        self.trust_score = trust_score
        self.status = status
        self.last_crawl_at = last_crawl_at
        self.failure_count = failure_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

class RobotsCheckResult:
    def __init__(self, url: str, can_crawl: bool, robots_content: Optional[str] = None,
                 user_agent_rules: Optional[Dict] = None, crawl_delay: Optional[int] = None):
        self.url = url
        self.can_crawl = can_crawl
        self.robots_content = robots_content
        self.user_agent_rules = user_agent_rules or {}
        self.crawl_delay = crawl_delay

class SourceMetricsUpdate:
    def __init__(self, source_id: int, success: bool, response_time_ms: Optional[int] = None,
                 documents_found: int = 0, quality_score: Optional[float] = None,
                 error_message: Optional[str] = None):
        self.source_id = source_id
        self.success = success
        self.response_time_ms = response_time_ms
        self.documents_found = documents_found
        self.quality_score = quality_score
        self.error_message = error_message