from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    KEYWORD_EXPANSION = "keyword_expansion"
    SOURCE_DISCOVERY = "source_discovery"
    CONTENT_COLLECTION = "content_collection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ALERT_GENERATION = "alert_generation"

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OsintTask:
    def __init__(self, id=None, task_type=TaskType.CONTENT_COLLECTION, keywords=None, 
                 sources=None, priority=TaskPriority.MEDIUM, status=TaskStatus.PENDING,
                 assigned_to=None, metadata=None, dependencies=None, retry_count=0,
                 max_retries=3, timeout_seconds=3600, expected_results=0):
        self.id = id
        self.task_type = task_type
        self.keywords = keywords or []
        self.sources = sources or []
        self.priority = priority
        self.status = status
        self.assigned_to = assigned_to
        self.metadata = metadata or {}
        self.dependencies = dependencies or []
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.expected_results = expected_results
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error_message = None

class TaskResult:
    def __init__(self, id=None, task_id=None, result_type="", data=None, 
                 quality_score=0.0, confidence_score=0.0):
        self.id = id
        self.task_id = task_id
        self.result_type = result_type
        self.data = data or {}
        self.quality_score = quality_score
        self.confidence_score = confidence_score
        self.created_at = datetime.utcnow()

class TaskQueue:
    def __init__(self, id=None, name="", queue_type="priority", max_workers=5,
                 status="active", metadata=None):
        self.id = id
        self.name = name
        self.queue_type = queue_type
        self.max_workers = max_workers
        self.status = status
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class TaskDependency:
    def __init__(self, id=None, task_id=None, depends_on_task_id=None, 
                 dependency_type="completion"):
        self.id = id
        self.task_id = task_id
        self.depends_on_task_id = depends_on_task_id
        self.dependency_type = dependency_type
        self.created_at = datetime.utcnow()

class WorkerNode:
    def __init__(self, id=None, node_id="", node_type="", capabilities=None,
                 max_concurrent_tasks=5, current_load=0, status="active",
                 last_heartbeat=None, metadata=None):
        self.id = id
        self.node_id = node_id
        self.node_type = node_type
        self.capabilities = capabilities or []
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_load = current_load
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()