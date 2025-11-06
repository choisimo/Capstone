from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CollectionStrategy(str, Enum):
    COMPREHENSIVE = "comprehensive"
    TARGETED = "targeted"
    MONITORING = "monitoring"
    HISTORICAL = "historical"


class SourceType(str, Enum):
    NEWS = "news"
    SOCIAL = "social"
    BLOG = "blog"
    FORUM = "forum"
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    CUSTOM = "custom"


class KeywordType(str, Enum):
    SEED = "seed"
    EXPANDED = "expanded"
    ALIAS = "alias"
    RELATED = "related"


class OsintPlan:
    def __init__(self, plan_id: Optional[str] = None, title: str = "", description: str = "",
                 query: str = "", objectives: Optional[List[str]] = None, 
                 strategy: CollectionStrategy = CollectionStrategy.TARGETED,
                 keywords: Optional[List[str]] = None, sources: Optional[List[Dict[str, Any]]] = None,
                 schedule: Optional[Dict[str, Any]] = None, status: PlanStatus = PlanStatus.DRAFT,
                 metadata: Optional[Dict[str, Any]] = None):
        self.plan_id = plan_id
        self.title = title
        self.description = description
        self.query = query
        self.objectives = objectives or []
        self.strategy = strategy
        self.keywords = keywords or []
        self.sources = sources or []
        self.schedule = schedule
        self.status = status
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = metadata or {}


class SourcePlan:
    def __init__(self, source_id: Optional[str] = None, source_type: SourceType = SourceType.NEWS,
                 name: str = "", url: str = "", priority: int = 5,
                 rate_limit: int = 10, is_active: bool = True,
                 config: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.source_id = source_id
        self.source_type = source_type
        self.name = name
        self.url = url
        self.priority = priority
        self.rate_limit = rate_limit
        self.is_active = is_active
        self.config = config or {}
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()


class KeywordPlan:
    def __init__(self, keyword_id: Optional[str] = None, term: str = "", lang: str = "ko",
                 keyword_type: KeywordType = KeywordType.SEED, importance: float = 1.0,
                 context: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.keyword_id = keyword_id
        self.term = term
        self.lang = lang
        self.keyword_type = keyword_type
        self.importance = importance
        self.context = context
        self.created_at = datetime.utcnow()
        self.metadata = metadata or {}


class CollectionSchedule:
    def __init__(self, schedule_id: Optional[str] = None, plan_id: str = "",
                 frequency: str = "daily", start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None, timezone: str = "UTC",
                 is_active: bool = True, metadata: Optional[Dict[str, Any]] = None):
        self.schedule_id = schedule_id
        self.plan_id = plan_id
        self.frequency = frequency
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
        self.timezone = timezone
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.metadata = metadata or {}


class PlanExecution:
    def __init__(self, execution_id: Optional[str] = None, plan_id: str = "",
                 status: str = "pending", started_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None, tasks_created: int = 0,
                 results_collected: int = 0, errors: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.execution_id = execution_id
        self.plan_id = plan_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.tasks_created = tasks_created
        self.results_collected = results_collected
        self.errors = errors or []
        self.created_at = datetime.utcnow()
        self.metadata = metadata or {}