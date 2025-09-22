from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    NEWS_COLLECTION = "news_collection"
    SOCIAL_MONITORING = "social_monitoring"
    WEB_SCRAPING = "web_scraping"
    API_COLLECTION = "api_collection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TREND_ANALYSIS = "trend_analysis"


class SourceType(str, Enum):
    NEWS = "news"
    SOCIAL = "social"
    BLOG = "blog"
    FORUM = "forum"
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    CUSTOM = "custom"


class OsintTask(BaseModel):
    id: str = Field(description="Unique task identifier")
    task_type: TaskType = Field(description="Type of OSINT task")
    keywords: List[str] = Field(description="Keywords for collection")
    sources: List[str] = Field(description="List of sources to collect from")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = Field(default=3600)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    expected_results: int = Field(default=0)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    id: str = Field(description="Unique result identifier")
    task_id: str = Field(description="Associated task ID")
    result_type: str = Field(description="Type of result")
    data: Dict[str, Any] = Field(description="Result data")
    quality_score: float = Field(default=0.0, description="Data quality score")
    confidence_score: float = Field(default=0.0, description="Result confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskQueue(BaseModel):
    queue_id: str = Field(description="Queue identifier")
    name: str = Field(description="Queue name")
    description: Optional[str] = None
    max_size: int = Field(default=1000)
    current_size: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskDependency(BaseModel):
    id: str = Field(description="Dependency identifier")
    task_id: str = Field(description="Dependent task ID")
    depends_on: str = Field(description="Task this depends on")
    dependency_type: str = Field(default="completion")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkerNode(BaseModel):
    id: str = Field(description="Worker identifier")
    node_id: str = Field(description="Physical node identifier")
    node_type: str = Field(description="Type of worker node")
    capabilities: List[str] = Field(description="Worker capabilities")
    status: str = Field(default="active")
    max_concurrent_tasks: int = Field(default=5)
    current_load: int = Field(default=0)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CollectionPlan(BaseModel):
    plan_id: str = Field(description="Unique plan identifier")
    query: str = Field(description="Search query or topic")
    objectives: List[str] = Field(description="Collection objectives")
    sources: List[Dict[str, Any]] = Field(description="Planned sources with configs")
    strategies: List[str] = Field(description="Collection strategies")
    keywords: List[str] = Field(description="Keywords for collection")
    filters: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceConfig(BaseModel):
    source_id: str = Field(description="Unique source identifier")
    source_type: SourceType
    name: str = Field(description="Source name")
    url: Optional[str] = None
    api_endpoint: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = Field(default=10, description="Requests per minute")
    priority: int = Field(default=5)
    is_active: bool = Field(default=True)
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStatus(BaseModel):
    workflow_id: str = Field(description="Workflow identifier")
    tasks: List[OsintTask] = Field(description="Tasks in workflow")
    status: TaskStatus
    progress: float = Field(default=0.0, description="Progress percentage")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    results_summary: Dict[str, Any] = Field(default_factory=dict)