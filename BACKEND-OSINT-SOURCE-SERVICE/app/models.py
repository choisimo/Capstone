from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class SourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING = "pending"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"

class SourceCategory(str, Enum):
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    BLOG = "blog"
    FORUM = "forum"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    ACADEMIC = "academic"
    FINANCIAL = "financial"
    TECHNOLOGY = "technology"
    OTHER = "other"

class SourceType(str, Enum):
    WEB = "web"
    RSS = "rss"
    API = "api"
    SOCIAL = "social"
    DATABASE = "database"

class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"

class Region(str, Enum):
    KR = "KR"
    US = "US"
    EU = "EU"
    GLOBAL = "GLOBAL"

class CrawlPolicy:
    def __init__(self, rate_limit: float = 1.0, max_depth: int = 3, 
                 timeout: int = 30, user_agent: str = "OSINT-Bot/1.0",
                 follow_redirects: bool = True, respect_robots: bool = True,
                 max_pages: Optional[int] = None, custom_headers: Optional[Dict] = None):
        self.rate_limit = rate_limit
        self.max_depth = max_depth
        self.timeout = timeout
        self.user_agent = user_agent
        self.follow_redirects = follow_redirects
        self.respect_robots = respect_robots
        self.max_pages = max_pages
        self.custom_headers = custom_headers or {}

class OsintSource:
    def __init__(self, id: Optional[str] = None, url: str = "", name: str = "",
                 description: str = "", host: str = "", category: SourceCategory = SourceCategory.OTHER,
                 source_type: SourceType = SourceType.WEB, region: Region = Region.KR,
                 trust_score: float = 0.5, reliability_score: float = 0.5,
                 crawl_policy: Optional[CrawlPolicy] = None, robots_txt: Optional[str] = None,
                 robots_checked_at: Optional[datetime] = None, last_crawl_at: Optional[datetime] = None,
                 last_success_at: Optional[datetime] = None, failure_count: int = 0,
                 consecutive_failures: int = 0, status: SourceStatus = SourceStatus.PENDING,
                 validation_status: ValidationStatus = ValidationStatus.PENDING,
                 metadata: Optional[Dict] = None, tags: Optional[List[str]] = None,
                 priority: int = 5, is_premium: bool = False):
        self.id = id
        self.url = url
        self.name = name
        self.description = description
        self.host = host
        self.category = category
        self.source_type = source_type
        self.region = region
        self.trust_score = trust_score
        self.reliability_score = reliability_score
        self.crawl_policy = crawl_policy or CrawlPolicy()
        self.robots_txt = robots_txt
        self.robots_checked_at = robots_checked_at
        self.last_crawl_at = last_crawl_at
        self.last_success_at = last_success_at
        self.failure_count = failure_count
        self.consecutive_failures = consecutive_failures
        self.status = status
        self.validation_status = validation_status
        self.metadata = metadata or {}
        self.tags = tags or []
        self.priority = priority
        self.is_premium = is_premium
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class SourceDiscovery:
    def __init__(self, id: Optional[str] = None, discovered_url: str = "",
                 discovered_via: str = "", discovery_method: str = "manual",
                 confidence_score: float = 0.5, suggested_category: Optional[SourceCategory] = None,
                 auto_validated: bool = False, needs_review: bool = True,
                 metadata: Optional[Dict] = None):
        self.id = id
        self.discovered_url = discovered_url
        self.discovered_via = discovered_via
        self.discovery_method = discovery_method
        self.confidence_score = confidence_score
        self.suggested_category = suggested_category
        self.auto_validated = auto_validated
        self.needs_review = needs_review
        self.metadata = metadata or {}
        self.discovered_at = datetime.utcnow()

class SourceValidationResult:
    def __init__(self, id: Optional[str] = None, source_id: Optional[str] = None,
                 is_accessible: bool = False, has_valid_content: bool = False,
                 content_quality_score: float = 0.0, language_detected: Optional[str] = None,
                 geo_location: Optional[str] = None, technology_stack: Optional[List[str]] = None,
                 validation_errors: Optional[List[str]] = None, 
                 validation_warnings: Optional[List[str]] = None,
                 recommendation: ValidationStatus = ValidationStatus.NEEDS_REVIEW):
        self.id = id
        self.source_id = source_id
        self.is_accessible = is_accessible
        self.has_valid_content = has_valid_content
        self.content_quality_score = content_quality_score
        self.language_detected = language_detected
        self.geo_location = geo_location
        self.technology_stack = technology_stack or []
        self.validation_errors = validation_errors or []
        self.validation_warnings = validation_warnings or []
        self.recommendation = recommendation
        self.validated_at = datetime.utcnow()

class OsintSourceTag:
    def __init__(self, id: Optional[str] = None, source_id: Optional[str] = None, 
                 tag: str = "", description: str = "", color: str = "#gray"):
        self.id = id
        self.source_id = source_id
        self.tag = tag
        self.description = description
        self.color = color
        self.created_at = datetime.utcnow()

class SourceMetrics:
    def __init__(self, id: Optional[str] = None, source_id: Optional[str] = None, 
                 date: Optional[datetime] = None, success_rate: float = 0.0,
                 avg_response_time: float = 0.0, documents_collected: int = 0, 
                 quality_score: float = 0.0, uptime_percentage: float = 0.0,
                 content_freshness_score: float = 0.0, unique_content_ratio: float = 0.0,
                 spam_score: float = 0.0, language_consistency_score: float = 0.0):
        self.id = id
        self.source_id = source_id
        self.date = date or datetime.utcnow()
        self.success_rate = success_rate
        self.avg_response_time = avg_response_time
        self.documents_collected = documents_collected
        self.quality_score = quality_score
        self.uptime_percentage = uptime_percentage
        self.content_freshness_score = content_freshness_score
        self.unique_content_ratio = unique_content_ratio
        self.spam_score = spam_score
        self.language_consistency_score = language_consistency_score

class SourceMonitoring:
    def __init__(self, id: Optional[str] = None, source_id: Optional[str] = None,
                 check_type: str = "availability", status: str = "pending",
                 response_time: Optional[float] = None, status_code: Optional[int] = None,
                 error_message: Optional[str] = None, content_hash: Optional[str] = None,
                 content_changed: bool = False, alert_triggered: bool = False):
        self.id = id
        self.source_id = source_id
        self.check_type = check_type
        self.status = status
        self.response_time = response_time
        self.status_code = status_code
        self.error_message = error_message
        self.content_hash = content_hash
        self.content_changed = content_changed
        self.alert_triggered = alert_triggered
        self.checked_at = datetime.utcnow()

class SourceReport:
    def __init__(self, id: Optional[str] = None, source_ids: Optional[List[str]] = None,
                 report_type: str = "summary", period_start: Optional[datetime] = None,
                 period_end: Optional[datetime] = None, total_sources: int = 0,
                 active_sources: int = 0, avg_quality_score: float = 0.0,
                 total_documents: int = 0, top_performers: Optional[List[Dict]] = None,
                 issues_detected: Optional[List[Dict]] = None, recommendations: Optional[List[str]] = None):
        self.id = id
        self.source_ids = source_ids or []
        self.report_type = report_type
        self.period_start = period_start
        self.period_end = period_end
        self.total_sources = total_sources
        self.active_sources = active_sources
        self.avg_quality_score = avg_quality_score
        self.total_documents = total_documents
        self.top_performers = top_performers or []
        self.issues_detected = issues_detected or []
        self.recommendations = recommendations or []
        self.generated_at = datetime.utcnow()