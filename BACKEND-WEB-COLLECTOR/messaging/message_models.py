"""
메시지 모델 정의
Kafka 메시지 스키마
"""
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import uuid


def generate_message_id() -> str:
    """메시지 ID 생성"""
    return str(uuid.uuid4())


class MessageType(str, Enum):
    """메시지 타입"""
    # 작업 관련
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # 크롤링 관련
    SCRAPE_REQUESTED = "scrape.requested"
    SCRAPE_COMPLETED = "scrape.completed"
    SCRAPE_FAILED = "scrape.failed"
    
    # 분석 관련
    ANALYSIS_REQUESTED = "analysis.requested"
    ANALYSIS_COMPLETED = "analysis.completed"
    
    # 모니터링 관련
    MONITOR_STARTED = "monitor.started"
    MONITOR_STOPPED = "monitor.stopped"
    CHANGE_DETECTED = "change.detected"
    
    # 시스템 관련
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


class Message(BaseModel):
    """기본 메시지 모델"""
    id: str = Field(default_factory=generate_message_id)
    type: MessageType
    source: str = Field(description="메시지 발송 서비스")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = Field(default=None, description="상관 관계 ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskMessage(Message):
    """작업 메시지"""
    task_id: str
    task_type: str
    status: str
    priority: str = "medium"
    config: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0


class EventMessage(Message):
    """이벤트 메시지"""
    event_type: str
    event_data: Dict[str, Any]
    severity: str = Field(default="info", description="이벤트 심각도")
    target: Optional[str] = Field(default=None, description="이벤트 대상")


class AnalysisMessage(Message):
    """분석 메시지"""
    content: str
    analysis_type: str
    language: str = "ko"
    result: Optional[Dict[str, Any]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MonitoringMessage(Message):
    """모니터링 메시지"""
    monitoring_id: str
    url: str
    change_type: Optional[str] = None
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    change_summary: Optional[str] = None
    notification_priority: str = "low"


class ScrapeMessage(Message):
    """스크래핑 메시지"""
    url: str
    strategy: str = "smart"
    prompt: Optional[str] = None
    target_fields: Optional[list] = None
    success: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class WorkflowMessage(Message):
    """워크플로우 메시지"""
    workflow_id: str
    workflow_name: str
    status: str
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    results: Optional[Dict[str, Any]] = None


class ScheduleMessage(Message):
    """스케줄 메시지"""
    schedule_id: str
    job_name: str
    schedule_type: str
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    enabled: bool = True
    error_count: int = 0


class MetricsMessage(Message):
    """메트릭 메시지"""
    component: str
    metrics: Dict[str, float]
    period: str = Field(default="1m", description="측정 주기")
    aggregation: str = Field(default="avg", description="집계 방식")


class AlertMessage(Message):
    """알림 메시지"""
    alert_type: str
    alert_level: str = Field(description="critical/high/medium/low")
    title: str
    description: str
    affected_component: Optional[str] = None
    resolution: Optional[str] = None
    auto_resolved: bool = False
