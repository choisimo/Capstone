from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Converted to Pydantic models for proper FastAPI validation & OpenAPI generation.

class TaskCreateRequest(BaseModel):
    task_type: str
    keywords: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    priority: str = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_seconds: int = 3600
    expected_results: int = 0

class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    task_type: str
    keywords: List[str]
    sources: List[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    metadata: Dict[str, Any]
    dependencies: List[str]
    retry_count: int
    max_retries: int
    timeout_seconds: int
    expected_results: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class TaskResultRequest(BaseModel):
    result_type: str
    data: Dict[str, Any]
    quality_score: float = 0.0
    confidence_score: float = 0.0

class TaskResultResponse(BaseModel):
    id: str
    task_id: str
    result_type: str
    data: Dict[str, Any]
    quality_score: float
    confidence_score: float
    created_at: datetime

class QueueStatsResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_completion_time: float
    queue_throughput: float

class WorkerRegistrationRequest(BaseModel):
    node_id: str
    node_type: str
    capabilities: List[str]
    max_concurrent_tasks: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkerResponse(BaseModel):
    id: str
    node_id: str
    node_type: str
    capabilities: List[str]
    max_concurrent_tasks: int
    current_load: int
    status: str
    last_heartbeat: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class TaskAssignmentRequest(BaseModel):
    worker_capabilities: List[str]
    max_tasks: int = 1

class TaskAssignmentResponse(BaseModel):
    tasks: List[TaskResponse]

class TaskListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[TaskResponse]
