"""
API 요청/응답 모델
Pydantic 모델 정의
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# === 공통 모델 ===

class ResponseStatus(str, Enum):
    """응답 상태"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"


class BaseResponse(BaseModel):
    """기본 응답 모델"""
    status: ResponseStatus
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseResponse):
    """에러 응답 모델"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# === 크롤링 관련 모델 ===

class ScrapeStrategy(str, Enum):
    """스크래핑 전략"""
    SMART = "smart"
    AI_LEARNING = "ai_learning"
    TEMPLATE_BASED = "template_based"
    STRUCTURED = "structured"


class ScrapeRequest(BaseModel):
    """스크래핑 요청"""
    url: HttpUrl
    prompt: Optional[str] = Field(
        default="Extract main content",
        description="AI extraction prompt"
    )
    strategy: ScrapeStrategy = Field(
        default=ScrapeStrategy.SMART,
        description="Scraping strategy"
    )
    target_fields: Optional[List[str]] = Field(
        default=None,
        description="Target fields to extract"
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached templates if available"
    )
    custom_headers: Optional[Dict[str, str]] = None


class ScrapeResponse(BaseResponse):
    """스크래핑 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    task_id: str
    data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0


# === 분석 관련 모델 ===

class AnalysisType(str, Enum):
    """분석 타입"""
    SENTIMENT = "sentiment"
    ABSA = "absa"
    KEYWORDS = "keywords"
    SUMMARY = "summary"
    NEWS_ANALYSIS = "news_analysis"
    PENSION_SENTIMENT = "pension_sentiment"


class AnalysisRequest(BaseModel):
    """분석 요청"""
    content: str = Field(..., description="Content to analyze")
    analysis_type: AnalysisType = Field(
        default=AnalysisType.SENTIMENT,
        description="Type of analysis"
    )
    language: str = Field(default="ko", description="Content language")
    additional_context: Optional[str] = None


class AnalysisResponse(BaseResponse):
    """분석 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    analysis_type: AnalysisType
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)


# === 모니터링 관련 모델 ===

class MonitoringStrategy(str, Enum):
    """모니터링 전략"""
    FULL_CONTENT = "full_content"
    SMART_DIFF = "smart_diff"
    STRUCTURE_ONLY = "structure_only"
    AI_ANALYSIS = "ai_analysis"
    KEYWORD_BASED = "keyword_based"


class MonitoringRequest(BaseModel):
    """모니터링 요청"""
    url: HttpUrl
    strategy: MonitoringStrategy = MonitoringStrategy.SMART_DIFF
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to track"
    )
    check_interval_minutes: int = Field(
        default=60,
        ge=1,
        le=10080,  # Max 1 week
        description="Check interval in minutes"
    )
    notification_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Change importance threshold for notification"
    )
    ai_analysis: bool = Field(
        default=True,
        description="Enable AI analysis"
    )


class MonitoringResponse(BaseResponse):
    """모니터링 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    monitoring_id: str
    url: str
    strategy: MonitoringStrategy
    next_check: datetime
    is_active: bool = True


class MonitoringStatusResponse(BaseResponse):
    """모니터링 상태 응답"""
    monitoring_id: str
    url: str
    is_active: bool
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    changes_detected: int = 0
    last_change: Optional[Dict[str, Any]] = None


# === 워크플로우 관련 모델 ===

class WorkflowStep(BaseModel):
    """워크플로우 스텝"""
    name: str
    type: str = Field(description="Step type: action, condition, parallel, loop")
    config: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)


class WorkflowRequest(BaseModel):
    """워크플로우 요청"""
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    initial_context: Dict[str, Any] = Field(default_factory=dict)
    start_step: Optional[str] = None


class WorkflowResponse(BaseResponse):
    """워크플로우 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    workflow_id: str
    name: str
    execution_status: str
    results: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseResponse):
    """워크플로우 상태 응답"""
    workflow_id: str
    name: str
    status: str
    current_step: Optional[str] = None
    steps_completed: int
    total_steps: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# === 작업 관련 모델 ===

class TaskPriority(str, Enum):
    """작업 우선순위"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class TaskRequest(BaseModel):
    """작업 요청"""
    task_type: str = Field(description="Task type")
    config: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseResponse):
    """작업 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    task_id: str
    task_type: str
    task_status: str


class TaskStatusResponse(BaseResponse):
    """작업 상태 응답"""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0


# === 스케줄 관련 모델 ===

class ScheduleType(str, Enum):
    """스케줄 타입"""
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    DAILY = "daily"
    WEEKLY = "weekly"


class ScheduleRequest(BaseModel):
    """스케줄 요청"""
    name: str
    task_type: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    task_config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ScheduleResponse(BaseResponse):
    """스케줄 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    schedule_id: str
    name: str
    next_run: Optional[datetime] = None


# === 시스템 관련 모델 ===

class SystemHealthResponse(BaseResponse):
    """시스템 헬스 체크 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    healthy: bool = True
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Component health status"
    )
    uptime: float = 0.0
    version: str = "1.0.0"


class SystemStatisticsResponse(BaseResponse):
    """시스템 통계 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    statistics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# === 템플릿 관련 모델 ===

class TemplateRequest(BaseModel):
    """템플릿 요청"""
    url: HttpUrl
    html_sample: Optional[str] = None
    target_fields: Optional[List[str]] = None
    auto_optimize: bool = True


class TemplateResponse(BaseResponse):
    """템플릿 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    template_id: str
    domain: str
    confidence: float
    selectors: Dict[str, Any]
    version: int = 1


# === 변경 감지 관련 모델 ===

class ChangeEvent(BaseModel):
    """변경 이벤트"""
    event_id: str
    url: str
    timestamp: datetime
    change_type: str
    importance_score: float
    change_summary: str
    notification_priority: str
    diff_details: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None


class ChangeHistoryResponse(BaseResponse):
    """변경 히스토리 응답"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    url: str
    total_changes: int
    changes: List[ChangeEvent]
