import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://pension_user:pension_pass@localhost:5432/pension_sentiment"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Service configuration
    service_name: str = "alert-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # API Keys for external services
    email_service_api_key: str = ""
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    
    # SMTP Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = "alerts@pensionsentiment.com"
    
    # Notification settings
    max_retries: int = 3
    retry_delay_seconds: int = 300  # 5 minutes
    batch_size: int = 100
    rate_limit_per_minute: int = 60
    
    # Alert thresholds and limits
    max_alerts_per_hour: int = 1000
    cooldown_override_enabled: bool = False
    
    # Notification channels
    enabled_channels: List[str] = ["email", "slack", "webhook"]
    
    # Webhook configuration
    webhook_timeout_seconds: int = 30
    webhook_retry_attempts: int = 3
    
    # Security
    api_key_header: str = "X-API-Key"
    allowed_origins: List[str] = ["*"]
    
    # Monitoring and logging
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # External service URLs
    analysis_service_url: str = "http://localhost:8001"
    collector_service_url: str = "http://localhost:8002"
    absa_service_url: str = "http://localhost:8003"
    
    # Template settings
    default_email_template: str = """
    <html>
        <body>
            <h2>{{alert_title}}</h2>
            <p><strong>Severity:</strong> {{severity}}</p>
            <p><strong>Service:</strong> {{source_service}}</p>
            <p><strong>Time:</strong> {{triggered_at}}</p>
            <p><strong>Message:</strong></p>
            <p>{{message}}</p>
            
            {% if triggered_data %}
            <h3>Alert Data:</h3>
            <pre>{{triggered_data | tojsonpretty}}</pre>
            {% endif %}
            
            <hr>
            <p><small>This is an automated alert from the Pension Sentiment Analysis Platform.</small></p>
        </body>
    </html>
    """
    
    default_slack_template: str = """
    :warning: *{{alert_title}}*
    
    *Severity:* {{severity}}
    *Service:* {{source_service}}
    *Time:* {{triggered_at}}
    
    {{message}}
    
    {% if actual_value and threshold_value %}
    *Value:* {{actual_value}} (threshold: {{threshold_value}})
    {% endif %}
    """
    
    # Quiet hours (when notifications should be reduced)
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    quiet_hours_timezone: str = "UTC"
    
    # Only send critical alerts during quiet hours
    quiet_hours_critical_only: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Alert type configurations
ALERT_TYPE_CONFIGS = {
    "sentiment_threshold": {
        "name": "Sentiment Threshold",
        "description": "Triggers when sentiment scores cross defined thresholds",
        "required_fields": ["threshold", "operator", "metric"],
        "operators": ["less_than", "greater_than", "equals", "not_equals"],
        "metrics": ["compound_score", "positive", "negative", "neutral"],
        "default_cooldown": 60,
        "template_vars": ["sentiment_score", "threshold", "metric"]
    },
    "volume_spike": {
        "name": "Volume Spike",
        "description": "Triggers when data volume increases significantly",
        "required_fields": ["spike_percentage", "time_window"],
        "time_windows": ["5m", "15m", "30m", "1h", "6h", "24h"],
        "default_cooldown": 30,
        "template_vars": ["current_volume", "previous_volume", "spike_percentage"]
    },
    "keyword_mention": {
        "name": "Keyword Mention",
        "description": "Triggers when specific keywords are mentioned frequently",
        "required_fields": ["keywords", "frequency", "time_window"],
        "default_cooldown": 15,
        "template_vars": ["keywords", "mention_count", "frequency_threshold"]
    },
    "trend_change": {
        "name": "Trend Change",
        "description": "Triggers when sentiment trends change direction",
        "required_fields": ["trend_direction", "duration", "confidence"],
        "trend_directions": ["positive", "negative", "neutral"],
        "default_cooldown": 120,
        "template_vars": ["old_trend", "new_trend", "confidence_score"]
    },
    "custom": {
        "name": "Custom Rule",
        "description": "Custom rules with flexible expressions",
        "required_fields": ["expression"],
        "default_cooldown": 60,
        "template_vars": ["expression_result", "variables"]
    }
}

# Notification channel configurations
CHANNEL_CONFIGS = {
    "email": {
        "name": "Email",
        "enabled": True,
        "rate_limit": 100,  # per hour
        "timeout_seconds": 30,
        "retry_delays": [60, 300, 900],  # 1min, 5min, 15min
        "max_content_length": 10000
    },
    "slack": {
        "name": "Slack",
        "enabled": True,
        "rate_limit": 200,  # per hour
        "timeout_seconds": 15,
        "retry_delays": [30, 180, 600],  # 30s, 3min, 10min
        "max_content_length": 4000
    },
    "webhook": {
        "name": "Webhook",
        "enabled": True,
        "rate_limit": 500,  # per hour
        "timeout_seconds": 30,
        "retry_delays": [60, 300, 900],
        "max_content_length": 50000
    },
    "sms": {
        "name": "SMS",
        "enabled": False,
        "rate_limit": 50,  # per hour
        "timeout_seconds": 10,
        "retry_delays": [120, 600, 1800],
        "max_content_length": 160
    }
}