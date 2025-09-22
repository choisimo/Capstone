from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class AlertType(str, Enum):
    SENTIMENT_THRESHOLD = "sentiment_threshold"
    VOLUME_SPIKE = "volume_spike"
    KEYWORD_MENTION = "keyword_mention"
    TREND_CHANGE = "trend_change"
    CUSTOM = "custom"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"

# Alert Rule Schemas
class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity = AlertSeverity.MEDIUM
    conditions: Dict[str, Any]
    notification_channels: List[str] = []
    notification_template: Optional[str] = None
    is_active: bool = True
    cooldown_minutes: int = Field(default=60, ge=0, le=10080)  # Max 1 week

class AlertRuleCreate(AlertRuleBase):
    created_by: Optional[str] = None

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    conditions: Optional[Dict[str, Any]] = None
    notification_channels: Optional[List[str]] = None
    notification_template: Optional[str] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0, le=10080)

class AlertRule(AlertRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True

# Alert Schemas
class AlertBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.PENDING
    triggered_data: Optional[Dict[str, Any]] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    source_service: Optional[str] = None
    source_data_id: Optional[str] = None
    tags: List[str] = []

class AlertCreate(AlertBase):
    rule_id: int

class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged_by: Optional[str] = None
    tags: Optional[List[str]] = None

class Alert(AlertBase):
    id: int
    rule_id: int
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True

class AlertWithRule(Alert):
    rule: AlertRule

# Notification Schemas
class NotificationBase(BaseModel):
    channel: NotificationChannel
    recipient: str
    subject: Optional[str] = None
    content: str

class NotificationCreate(NotificationBase):
    alert_id: int

class NotificationUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None

class Notification(NotificationBase):
    id: int
    alert_id: int
    status: str = "pending"
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Alert History Schemas
class AlertHistoryBase(BaseModel):
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertHistoryCreate(AlertHistoryBase):
    alert_id: int

class AlertHistory(AlertHistoryBase):
    id: int
    alert_id: int
    performed_at: datetime

    class Config:
        from_attributes = True

# Alert Subscription Schemas
class AlertSubscriptionBase(BaseModel):
    user_id: str
    user_email: EmailStr
    alert_types: List[AlertType] = []
    severities: List[AlertSeverity] = []
    channels: List[NotificationChannel] = []
    keywords: List[str] = []
    sources: List[str] = []
    is_active: bool = True
    quiet_hours_start: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = "UTC"

class AlertSubscriptionCreate(AlertSubscriptionBase):
    pass

class AlertSubscriptionUpdate(BaseModel):
    alert_types: Optional[List[AlertType]] = None
    severities: Optional[List[AlertSeverity]] = None
    channels: Optional[List[NotificationChannel]] = None
    keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    is_active: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None

class AlertSubscription(AlertSubscriptionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Trigger Alert Schemas
class TriggerAlertRequest(BaseModel):
    rule_id: int
    triggered_data: Dict[str, Any]
    actual_value: Optional[float] = None
    source_service: str
    source_data_id: Optional[str] = None
    custom_message: Optional[str] = None

class BulkAlertRequest(BaseModel):
    alerts: List[TriggerAlertRequest]

# Response Schemas
class AlertResponse(BaseModel):
    success: bool
    message: str
    alert_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

class BulkAlertResponse(BaseModel):
    success: bool
    created_count: int
    failed_count: int
    created_alerts: List[int] = []
    errors: List[str] = []

class AlertStats(BaseModel):
    total_alerts: int
    pending_alerts: int
    active_alerts: int
    resolved_alerts: int
    critical_alerts: int
    alerts_last_24h: int
    alerts_by_severity: Dict[str, int]
    alerts_by_type: Dict[str, int]

class NotificationStats(BaseModel):
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    channels_breakdown: Dict[str, int]

# Rule Testing Schemas
class TestRuleRequest(BaseModel):
    rule_id: int
    test_data: Dict[str, Any]

class TestRuleResponse(BaseModel):
    would_trigger: bool
    matched_conditions: List[str]
    message_preview: str
    estimated_recipients: int

# Dashboard Schemas
class AlertDashboard(BaseModel):
    alert_stats: AlertStats
    notification_stats: NotificationStats
    recent_alerts: List[Alert]
    active_rules: List[AlertRule]
    top_alert_sources: List[Dict[str, Union[str, int]]]