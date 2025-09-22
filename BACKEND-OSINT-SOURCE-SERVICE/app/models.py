from typing import Optional, Dict
from datetime import datetime

class SourceStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING = "pending"

class SourceCategory:
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    BLOG = "blog"
    FORUM = "forum"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    ACADEMIC = "academic"
    OTHER = "other"

class OsintSource:
    def __init__(self, id=None, url="", host="", category=SourceCategory.OTHER, 
                 region="KR", trust_score=0.5, crawl_policy=None, robots_txt=None,
                 robots_checked_at=None, last_crawl_at=None, last_success_at=None,
                 failure_count=0, status=SourceStatus.PENDING, metadata=None):
        self.id = id
        self.url = url
        self.host = host
        self.category = category
        self.region = region
        self.trust_score = trust_score
        self.crawl_policy = crawl_policy or {
            "rate_limit": 1.0,
            "max_depth": 3,
            "timeout": 30,
            "user_agent": "OSINT-Bot/1.0",
            "follow_redirects": True
        }
        self.robots_txt = robots_txt
        self.robots_checked_at = robots_checked_at
        self.last_crawl_at = last_crawl_at
        self.last_success_at = last_success_at
        self.failure_count = failure_count
        self.status = status
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class OsintSourceTag:
    def __init__(self, id=None, source_id=None, tag=""):
        self.id = id
        self.source_id = source_id
        self.tag = tag
        self.created_at = datetime.utcnow()

class SourceMetrics:
    def __init__(self, id=None, source_id=None, date=None, success_rate=0.0,
                 avg_response_time=0.0, documents_collected=0, quality_score=0.0):
        self.id = id
        self.source_id = source_id
        self.date = date or datetime.utcnow()
        self.success_rate = success_rate
        self.avg_response_time = avg_response_time
        self.documents_collected = documents_collected
        self.quality_score = quality_score