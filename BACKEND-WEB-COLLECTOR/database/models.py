"""
데이터베이스 모델 정의
SQLAlchemy ORM 모델
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """UUID 생성"""
    return str(uuid.uuid4())


class Task(Base):
    """작업 테이블"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(String(20), nullable=False, default="medium")
    config = Column(JSON, default={})
    result = Column(JSON, default=None)
    error = Column(Text, default=None)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, default=None)
    completed_at = Column(DateTime, default=None)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_created', 'created_at'),
    )


class ScrapeResult(Base):
    """스크래핑 결과 테이블"""
    __tablename__ = "scrape_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey('tasks.id'), nullable=False)
    url = Column(Text, nullable=False)
    strategy = Column(String(50), nullable=False)
    success = Column(Boolean, default=False)
    data = Column(JSON, default={})
    html_content = Column(Text, default=None)
    execution_time = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    task = relationship("Task", backref="scrape_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_scrape_url', 'url'),
        Index('idx_scrape_created', 'created_at'),
    )


class AnalysisResult(Base):
    """분석 결과 테이블"""
    __tablename__ = "analysis_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_hash = Column(String(64), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    result = Column(JSON, nullable=False)
    confidence = Column(Float, default=0.0)
    language = Column(String(10), default="ko")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_hash', 'content_hash'),
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_created', 'created_at'),
    )


class MonitoringConfig(Base):
    """모니터링 설정 테이블"""
    __tablename__ = "monitoring_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(Text, nullable=False)
    strategy = Column(String(50), nullable=False)
    keywords = Column(JSON, default=[])
    check_interval_minutes = Column(Integer, default=60)
    notification_threshold = Column(Float, default=0.3)
    ai_analysis = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check = Column(DateTime, default=None)
    next_check = Column(DateTime, default=None)
    metadata = Column(JSON, default={})
    
    # Relationships
    change_events = relationship("ChangeEvent", back_populates="monitoring")
    
    # Indexes
    __table_args__ = (
        Index('idx_monitor_url', 'url'),
        Index('idx_monitor_active', 'is_active'),
        Index('idx_monitor_next_check', 'next_check'),
    )


class ChangeEvent(Base):
    """변경 이벤트 테이블"""
    __tablename__ = "change_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    monitoring_id = Column(String(36), ForeignKey('monitoring_configs.id'), nullable=False)
    url = Column(Text, nullable=False)
    change_type = Column(String(50), nullable=False)
    importance_score = Column(Float, default=0.0)
    change_summary = Column(Text, default="")
    notification_priority = Column(String(20), default="low")
    before_content = Column(Text, default=None)
    after_content = Column(Text, default=None)
    diff_details = Column(JSON, default={})
    ai_analysis = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    monitoring = relationship("MonitoringConfig", back_populates="change_events")
    
    # Indexes
    __table_args__ = (
        Index('idx_change_monitoring', 'monitoring_id'),
        Index('idx_change_created', 'created_at'),
        Index('idx_change_importance', 'importance_score'),
    )


class Template(Base):
    """추출 템플릿 테이블"""
    __tablename__ = "templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    template_id = Column(String(50), unique=True, nullable=False)
    domain = Column(String(255), nullable=False)
    url_pattern = Column(Text, nullable=False)
    selectors = Column(JSON, nullable=False)
    confidence = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_template_domain', 'domain'),
        Index('idx_template_confidence', 'confidence'),
        UniqueConstraint('template_id', name='uq_template_id'),
    )


class WorkflowExecution(Base):
    """워크플로우 실행 테이블"""
    __tablename__ = "workflow_executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default=None)
    status = Column(String(20), nullable=False, default="pending")
    current_step = Column(String(255), default=None)
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    context = Column(JSON, default={})
    results = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, default=None)
    completed_at = Column(DateTime, default=None)
    error = Column(Text, default=None)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_status', 'status'),
        Index('idx_workflow_created', 'created_at'),
    )


class ScheduledJob(Base):
    """스케줄된 작업 테이블"""
    __tablename__ = "scheduled_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)
    schedule_type = Column(String(20), nullable=False)
    schedule_config = Column(JSON, nullable=False)
    task_config = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, default=None)
    next_run = Column(DateTime, default=None)
    run_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_schedule_enabled', 'enabled'),
        Index('idx_schedule_next_run', 'next_run'),
        UniqueConstraint('job_id', name='uq_job_id'),
    )


class SystemMetrics(Base):
    """시스템 메트릭 테이블"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_component', 'component'),
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_name', 'metric_name'),
    )
