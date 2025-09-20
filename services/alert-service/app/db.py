from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from enum import Enum
import datetime

SQLALCHEMY_DATABASE_URL = "postgresql://pension_user:pension_pass@localhost:5432/pension_sentiment"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default=AlertSeverity.MEDIUM)
    
    # Rule conditions (stored as JSON for flexibility)
    conditions = Column(JSON, nullable=False)
    
    # Notification settings
    notification_channels = Column(JSON, default=list)
    notification_template = Column(Text)
    
    # Rule status and timing
    is_active = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=60)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    alerts = relationship("Alert", back_populates="rule")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    
    # Alert details
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=AlertStatus.PENDING)
    
    # Alert data
    triggered_data = Column(JSON)  # The data that triggered the alert
    threshold_value = Column(Float)
    actual_value = Column(Float)
    
    # Timing
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    
    # Metadata
    source_service = Column(String(100))  # e.g., "analysis-service"
    source_data_id = Column(String(100))  # Reference to source data
    tags = Column(JSON, default=list)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # Notification details
    channel = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)  # email, phone, webhook URL, etc.
    subject = Column(String(255))
    content = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, sent, failed, delivered
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    
    # External reference (for tracking delivery status)
    external_id = Column(String(255))  # Message ID from external service
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")

class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # History tracking
    action = Column(String(100), nullable=False)  # created, acknowledged, resolved, etc.
    old_status = Column(String(20))
    new_status = Column(String(20))
    
    # Action details
    performed_by = Column(String(100))
    notes = Column(Text)
    
    # Timing
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    metadata = Column(JSON)

class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Subscription details
    user_id = Column(String(100), nullable=False)
    user_email = Column(String(255), nullable=False)
    
    # Subscription preferences
    alert_types = Column(JSON, default=list)  # Which alert types to subscribe to
    severities = Column(JSON, default=list)   # Which severities to receive
    channels = Column(JSON, default=list)     # Preferred notification channels
    
    # Filters
    keywords = Column(JSON, default=list)     # Only alerts containing these keywords
    sources = Column(JSON, default=list)      # Only alerts from these sources
    
    # Schedule
    is_active = Column(Boolean, default=True)
    quiet_hours_start = Column(String(5))     # e.g., "22:00"
    quiet_hours_end = Column(String(5))       # e.g., "08:00"
    timezone = Column(String(50), default="UTC")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())