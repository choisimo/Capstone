from typing import List, Optional, Dict, Any
from datetime import datetime

class TaskCreateRequest:
    def __init__(self, task_type: str, keywords: List[str] = None, 
                 sources: List[str] = None, priority: str = "medium",
                 metadata: Dict[str, Any] = None, dependencies: List[str] = None,
                 timeout_seconds: int = 3600, expected_results: int = 0):
        self.task_type = task_type
        self.keywords = keywords or []
        self.sources = sources or []
        self.priority = priority
        self.metadata = metadata or {}
        self.dependencies = dependencies or []
        self.timeout_seconds = timeout_seconds
        self.expected_results = expected_results

class TaskUpdateRequest:
    def __init__(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
                 priority: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                 error_message: Optional[str] = None):
        self.status = status
        self.assigned_to = assigned_to
        self.priority = priority
        self.metadata = metadata
        self.error_message = error_message

class TaskResponse:
    def __init__(self, id: str, task_type: str, keywords: List[str], sources: List[str],
                 priority: str, status: str, assigned_to: Optional[str], metadata: Dict[str, Any],
                 dependencies: List[str], retry_count: int, max_retries: int,
                 timeout_seconds: int, expected_results: int, created_at: datetime,
                 updated_at: datetime, started_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None, error_message: Optional[str] = None):
        self.id = id
        self.task_type = task_type
        self.keywords = keywords
        self.sources = sources
        self.priority = priority
        self.status = status
        self.assigned_to = assigned_to
        self.metadata = metadata
        self.dependencies = dependencies
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.expected_results = expected_results
        self.created_at = created_at
        self.updated_at = updated_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.error_message = error_message

class TaskResultRequest:
    def __init__(self, result_type: str, data: Dict[str, Any], 
                 quality_score: float = 0.0, confidence_score: float = 0.0):
        self.result_type = result_type
        self.data = data
        self.quality_score = quality_score
        self.confidence_score = confidence_score

class TaskResultResponse:
    def __init__(self, id: str, task_id: str, result_type: str, data: Dict[str, Any],
                 quality_score: float, confidence_score: float, created_at: datetime):
        self.id = id
        self.task_id = task_id
        self.result_type = result_type
        self.data = data
        self.quality_score = quality_score
        self.confidence_score = confidence_score
        self.created_at = created_at

class QueueStatsResponse:
    def __init__(self, total_tasks: int, pending_tasks: int, in_progress_tasks: int,
                 completed_tasks: int, failed_tasks: int, average_completion_time: float,
                 queue_throughput: float):
        self.total_tasks = total_tasks
        self.pending_tasks = pending_tasks
        self.in_progress_tasks = in_progress_tasks
        self.completed_tasks = completed_tasks
        self.failed_tasks = failed_tasks
        self.average_completion_time = average_completion_time
        self.queue_throughput = queue_throughput

class WorkerRegistrationRequest:
    def __init__(self, node_id: str, node_type: str, capabilities: List[str],
                 max_concurrent_tasks: int = 5, metadata: Dict[str, Any] = None):
        self.node_id = node_id
        self.node_type = node_type
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        self.metadata = metadata or {}

class WorkerResponse:
    def __init__(self, id: str, node_id: str, node_type: str, capabilities: List[str],
                 max_concurrent_tasks: int, current_load: int, status: str,
                 last_heartbeat: Optional[datetime], metadata: Dict[str, Any],
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.node_id = node_id
        self.node_type = node_type
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_load = current_load
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.metadata = metadata
        self.created_at = created_at
        self.updated_at = updated_at

class TaskAssignmentRequest:
    def __init__(self, worker_capabilities: List[str], max_tasks: int = 1):
        self.worker_capabilities = worker_capabilities
        self.max_tasks = max_tasks

class TaskAssignmentResponse:
    def __init__(self, tasks: List[TaskResponse]):
        self.tasks = tasks