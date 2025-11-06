from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Schemas
class SourceRegisterRequest:
    def __init__(self, url: str, name: str = "", description: str = "",
                 category: str = "other", source_type: str = "web", 
                 region: str = "KR", priority: int = 5, 
                 is_premium: bool = False, tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.url = url
        self.name = name
        self.description = description
        self.category = category
        self.source_type = source_type
        self.region = region
        self.priority = priority
        self.is_premium = is_premium
        self.tags = tags or []
        self.metadata = metadata or {}

class BulkSourceRegisterRequest:
    def __init__(self, sources: List[Dict[str, Any]]):
        self.sources = sources

class SourceUpdateRequest:
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None,
                 category: Optional[str] = None, source_type: Optional[str] = None,
                 region: Optional[str] = None, status: Optional[str] = None,
                 priority: Optional[int] = None, is_premium: Optional[bool] = None,
                 tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.category = category
        self.source_type = source_type
        self.region = region
        self.status = status
        self.priority = priority
        self.is_premium = is_premium
        self.tags = tags
        self.metadata = metadata

class SourceDiscoveryRequest:
    def __init__(self, seed_urls: List[str], max_depth: int = 2,
                 discovery_filters: Optional[Dict[str, Any]] = None):
        self.seed_urls = seed_urls
        self.max_depth = max_depth
        self.discovery_filters = discovery_filters or {}

class SourceValidationRequest:
    def __init__(self, url: str, check_content: bool = True,
                 check_robots: bool = True, timeout: int = 30):
        self.url = url
        self.check_content = check_content
        self.check_robots = check_robots
        self.timeout = timeout

class SourceMonitoringRequest:
    def __init__(self, check_type: str = "availability", 
                 timeout: int = 30, follow_redirects: bool = True):
        self.check_type = check_type
        self.timeout = timeout
        self.follow_redirects = follow_redirects

class SourceReportRequest:
    def __init__(self, source_ids: Optional[List[str]] = None,
                 period_days: int = 7, report_type: str = "summary",
                 include_metrics: bool = True, include_issues: bool = True):
        self.source_ids = source_ids
        self.period_days = period_days
        self.report_type = report_type
        self.include_metrics = include_metrics
        self.include_issues = include_issues

# Response Schemas
class SourceResponse:
    def __init__(self, id: str, url: str, name: str, description: str,
                 host: str, category: str, source_type: str, region: str,
                 status: str, validation_status: str, trust_score: float,
                 reliability_score: float, priority: int, is_premium: bool,
                 tags: List[str], metadata: Dict[str, Any],
                 robots_txt: Optional[str] = None, 
                 robots_checked_at: Optional[str] = None,
                 last_crawl_at: Optional[str] = None,
                 last_success_at: Optional[str] = None,
                 failure_count: int = 0, consecutive_failures: int = 0,
                 created_at: str = "", updated_at: str = ""):
        self.id = id
        self.url = url
        self.name = name
        self.description = description
        self.host = host
        self.category = category
        self.source_type = source_type
        self.region = region
        self.status = status
        self.validation_status = validation_status
        self.trust_score = trust_score
        self.reliability_score = reliability_score
        self.priority = priority
        self.is_premium = is_premium
        self.tags = tags
        self.metadata = metadata
        self.robots_txt = robots_txt
        self.robots_checked_at = robots_checked_at
        self.last_crawl_at = last_crawl_at
        self.last_success_at = last_success_at
        self.failure_count = failure_count
        self.consecutive_failures = consecutive_failures
        self.created_at = created_at
        self.updated_at = updated_at

class SourceListResponse:
    def __init__(self, sources: List[Dict[str, Any]], total: int, 
                 offset: int, limit: int):
        self.sources = sources
        self.total = total
        self.offset = offset
        self.limit = limit

class SourceDiscoveryResponse:
    def __init__(self, id: str, discovered_url: str, discovered_via: str,
                 discovery_method: str, confidence_score: float,
                 suggested_category: Optional[str] = None,
                 auto_validated: bool = False, needs_review: bool = True,
                 discovered_at: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.discovered_url = discovered_url
        self.discovered_via = discovered_via
        self.discovery_method = discovery_method
        self.confidence_score = confidence_score
        self.suggested_category = suggested_category
        self.auto_validated = auto_validated
        self.needs_review = needs_review
        self.discovered_at = discovered_at
        self.metadata = metadata or {}

class SourceValidationResponse:
    def __init__(self, validation_id: str, url: str, is_accessible: bool,
                 has_valid_content: bool, content_quality_score: float,
                 language_detected: Optional[str] = None,
                 geo_location: Optional[str] = None,
                 technology_stack: Optional[List[str]] = None,
                 validation_errors: Optional[List[str]] = None,
                 validation_warnings: Optional[List[str]] = None,
                 recommendation: str = "needs_review",
                 validated_at: str = ""):
        self.validation_id = validation_id
        self.url = url
        self.is_accessible = is_accessible
        self.has_valid_content = has_valid_content
        self.content_quality_score = content_quality_score
        self.language_detected = language_detected
        self.geo_location = geo_location
        self.technology_stack = technology_stack or []
        self.validation_errors = validation_errors or []
        self.validation_warnings = validation_warnings or []
        self.recommendation = recommendation
        self.validated_at = validated_at

class SourceMonitoringResponse:
    def __init__(self, monitoring_id: str, source_id: str, check_type: str,
                 status: str, response_time: Optional[float] = None,
                 status_code: Optional[int] = None, error_message: Optional[str] = None,
                 content_hash: Optional[str] = None, content_changed: bool = False,
                 alert_triggered: bool = False, checked_at: str = ""):
        self.monitoring_id = monitoring_id
        self.source_id = source_id
        self.check_type = check_type
        self.status = status
        self.response_time = response_time
        self.status_code = status_code
        self.error_message = error_message
        self.content_hash = content_hash
        self.content_changed = content_changed
        self.alert_triggered = alert_triggered
        self.checked_at = checked_at

class SourceReportResponse:
    def __init__(self, report_id: str, report_type: str,
                 period_start: Optional[str] = None, period_end: Optional[str] = None,
                 summary: Optional[Dict[str, Any]] = None,
                 top_performers: Optional[List[Dict[str, Any]]] = None,
                 issues_detected: Optional[List[Dict[str, Any]]] = None,
                 recommendations: Optional[List[str]] = None,
                 generated_at: str = ""):
        self.report_id = report_id
        self.report_type = report_type
        self.period_start = period_start
        self.period_end = period_end
        self.summary = summary or {}
        self.top_performers = top_performers or []
        self.issues_detected = issues_detected or []
        self.recommendations = recommendations or []
        self.generated_at = generated_at

class BulkOperationResponse:
    def __init__(self, message: str, summary: Dict[str, int],
                 details: Dict[str, List[Dict[str, Any]]]):
        self.message = message
        self.summary = summary
        self.details = details

class CrawlableSourceResponse:
    def __init__(self, id: str, url: str, host: str, category: str,
                 trust_score: float, crawl_policy: Dict[str, Any],
                 last_crawl_at: Optional[str] = None):
        self.id = id
        self.url = url
        self.host = host
        self.category = category
        self.trust_score = trust_score
        self.crawl_policy = crawl_policy
        self.last_crawl_at = last_crawl_at

# Common Response Schema
class APIResponse:
    def __init__(self, status: str = "success", message: str = "",
                 data: Optional[Any] = None, error: Optional[str] = None,
                 timestamp: Optional[str] = None):
        self.status = status
        self.message = message
        self.data = data
        self.error = error
        self.timestamp = timestamp or datetime.utcnow().isoformat()

# Utility functions for schema validation
def validate_source_category(category: str) -> bool:
    """Validate source category"""
    valid_categories = [
        "news", "social_media", "blog", "forum", "government", 
        "corporate", "academic", "financial", "technology", "other"
    ]
    return category in valid_categories

def validate_source_type(source_type: str) -> bool:
    """Validate source type"""
    valid_types = ["web", "rss", "api", "social", "database"]
    return source_type in valid_types

def validate_region(region: str) -> bool:
    """Validate region"""
    valid_regions = ["KR", "US", "EU", "GLOBAL"]
    return region in valid_regions

def validate_source_status(status: str) -> bool:
    """Validate source status"""
    valid_statuses = ["active", "inactive", "blocked", "pending", "error", "rate_limited"]
    return status in valid_statuses

def validate_validation_status(status: str) -> bool:
    """Validate validation status"""
    valid_statuses = ["pending", "valid", "invalid", "needs_review"]
    return status in valid_statuses

def validate_url(url: str) -> bool:
    """Basic URL validation"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

# Schema factory functions
def create_source_response_from_model(source) -> Dict[str, Any]:
    """Create API response from source model"""
    return {
        "id": source.id,
        "url": source.url,
        "name": source.name,
        "description": source.description,
        "host": source.host,
        "category": source.category.value if hasattr(source.category, 'value') else source.category,
        "source_type": source.source_type.value if hasattr(source.source_type, 'value') else source.source_type,
        "region": source.region.value if hasattr(source.region, 'value') else source.region,
        "status": source.status.value if hasattr(source.status, 'value') else source.status,
        "validation_status": source.validation_status.value if hasattr(source.validation_status, 'value') else source.validation_status,
        "trust_score": source.trust_score,
        "reliability_score": source.reliability_score,
        "priority": source.priority,
        "is_premium": source.is_premium,
        "tags": source.tags,
        "metadata": source.metadata,
        "robots_txt": source.robots_txt,
        "robots_checked_at": source.robots_checked_at.isoformat() if source.robots_checked_at else None,
        "last_crawl_at": source.last_crawl_at.isoformat() if source.last_crawl_at else None,
        "last_success_at": source.last_success_at.isoformat() if source.last_success_at else None,
        "failure_count": source.failure_count,
        "consecutive_failures": source.consecutive_failures,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None
    }

def create_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "status": "error",
        "error": error_message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }