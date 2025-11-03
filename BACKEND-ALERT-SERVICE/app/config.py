"""Alert Service configuration module backed by Consul."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config_loader import load_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)

    # Core
    PORT: int = Field(default=8004)
    DEBUG: bool = Field(default=False)
    SERVICE_NAME: str = Field(default="alert-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")

    # Dependencies (required)
    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)

    # External service URLs
    ANALYSIS_SERVICE_URL: str = Field(default="http://analysis-service:8001")
    COLLECTOR_SERVICE_URL: str = Field(default="http://collector-service:8002")
    ABSA_SERVICE_URL: str = Field(default="http://absa-service:8003")

    # Eureka discovery (optional)
    EUREKA_ENABLED: bool = Field(default=False)
    EUREKA_SERVICE_URLS: Optional[str] = Field(default=None)
    EUREKA_APP_NAME: str = Field(default="alert-service")
    EUREKA_INSTANCE_HOST: Optional[str] = Field(default=None)
    EUREKA_INSTANCE_IP: Optional[str] = Field(default=None)
    EUREKA_METADATA: Optional[str] = Field(default=None)

    # Secrets / credentials
    EMAIL_SERVICE_API_KEY: SecretStr | None = Field(default=None)
    SLACK_WEBHOOK_URL: SecretStr | None = Field(default=None)
    SLACK_BOT_TOKEN: SecretStr | None = Field(default=None)
    TWILIO_ACCOUNT_SID: SecretStr | None = Field(default=None)
    TWILIO_AUTH_TOKEN: SecretStr | None = Field(default=None)
    SMTP_USERNAME: SecretStr | None = Field(default=None)
    SMTP_PASSWORD: SecretStr | None = Field(default=None)

    # SMTP settings
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USE_TLS: bool = Field(default=True)
    SMTP_FROM_EMAIL: str = Field(default="alerts@pensionsentiment.com")

    # Notification behaviour
    MAX_RETRIES: int = Field(default=3)
    RETRY_DELAY_SECONDS: int = Field(default=300)
    BATCH_SIZE: int = Field(default=100)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    MAX_ALERTS_PER_HOUR: int = Field(default=1000)
    COOLDOWN_OVERRIDE_ENABLED: bool = Field(default=False)
    ENABLED_CHANNELS: List[str] = Field(default_factory=lambda: ["email", "slack", "webhook"])
    SLACK_CHANNEL: Optional[str] = Field(default=None)

    # Webhook
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=30)
    WEBHOOK_RETRY_ATTEMPTS: int = Field(default=3)

    # Security/CORS
    API_KEY_HEADER: str = Field(default="X-API-Key")
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Monitoring
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)

    # Templates
    DEFAULT_EMAIL_TEMPLATE: str = Field(
        default=(
            """
    <html>
        <body>
            <h2>{{alert_title}}</h2>
            <p><strong>심각도:</strong> {{severity}}</p>
            <p><strong>서비스:</strong> {{source_service}}</p>
            <p><strong>시간:</strong> {{triggered_at}}</p>
            <p><strong>메시지:</strong></p>
            <p>{{message}}</p>
            
            {% if triggered_data %}
            <h3>알림 데이터:</h3>
            <pre>{{triggered_data | tojsonpretty}}</pre>
            {% endif %}
            
            <hr>
            <p><small>연금 감성 분석 플랫폼에서 자동 발송된 알림입니다.</small></p>
        </body>
    </html>
            """
        )
    )
    DEFAULT_SLACK_TEMPLATE: str = Field(
        default=(
            """
    :warning: *{{alert_title}}*
    
    *심각도:* {{severity}}
    *서비스:* {{source_service}}
    *시간:* {{triggered_at}}
    
    {{message}}
    
    {% if actual_value and threshold_value %}
    *현재 값:* {{actual_value}} (임계값: {{threshold_value}})
    {% endif %}
            """
        )
    )

    # Quiet hours
    QUIET_HOURS_ENABLED: bool = Field(default=True)
    QUIET_HOURS_START: str = Field(default="22:00")
    QUIET_HOURS_END: str = Field(default="08:00")
    QUIET_HOURS_TIMEZONE: str = Field(default="UTC")
    QUIET_HOURS_CRITICAL_ONLY: bool = Field(default=True)

    CONFIG_SYNC_TIMESTAMP: Optional[str] = None


def _load_settings() -> Settings:
    required = [
        "DATABASE_URL",
        "REDIS_URL",
    ]
    return load_settings("alert-service", settings_cls=Settings, require=required)


settings = _load_settings()

# 알림 타입 설정
ALERT_TYPE_CONFIGS = {
    "sentiment_threshold": {  # 감성 임계값 알림
        "name": "Sentiment Threshold",
        "description": "감성 점수가 임계값을 초과할 때 트리거",
        "required_fields": ["threshold", "operator", "metric"],  # 필수 필드
        "operators": ["less_than", "greater_than", "equals", "not_equals"],  # 비교 연산자
        "metrics": ["compound_score", "positive", "negative", "neutral"],  # 메트릭 타입
        "default_cooldown": 60,  # 기본 쿨다운 시간(초)
        "template_vars": ["sentiment_score", "threshold", "metric"]  # 템플릿 변수
    },
    "volume_spike": {  # 볼륨 급증 알림
        "name": "Volume Spike",
        "description": "데이터 볼륨이 크게 증가할 때 트리거",
        "required_fields": ["spike_percentage", "time_window"],  # 필수 필드
        "time_windows": ["5m", "15m", "30m", "1h", "6h", "24h"],  # 시간 윈도우 옵션
        "default_cooldown": 30,  # 기본 쿨다운 시간(초)
        "template_vars": ["current_volume", "previous_volume", "spike_percentage"]  # 템플릿 변수
    },
    "keyword_mention": {  # 키워드 언급 알림
        "name": "Keyword Mention",
        "description": "특정 키워드가 빈번히 언급될 때 트리거",
        "required_fields": ["keywords", "frequency", "time_window"],  # 필수 필드
        "default_cooldown": 15,  # 기본 쿨다운 시간(초)
        "template_vars": ["keywords", "mention_count", "frequency_threshold"]  # 템플릿 변수
    },
    "trend_change": {  # 트렌드 변화 알림
        "name": "Trend Change",
        "description": "감성 트렌드가 방향을 바꿀 때 트리거",
        "required_fields": ["trend_direction", "duration", "confidence"],  # 필수 필드
        "trend_directions": ["positive", "negative", "neutral"],  # 트렌드 방향 옵션
        "default_cooldown": 120,  # 기본 쿨다운 시간(초)
        "template_vars": ["old_trend", "new_trend", "confidence_score"]  # 템플릿 변수
    },
    "custom": {  # 사용자 정의 규칙
        "name": "Custom Rule",
        "description": "유연한 표현식을 사용한 사용자 정의 규칙",
        "required_fields": ["expression"],  # 필수 필드
        "default_cooldown": 60,  # 기본 쿨다운 시간(초)
        "template_vars": ["expression_result", "variables"]  # 템플릿 변수
    }
}

# 알림 채널 설정
CHANNEL_CONFIGS = {
    "email": {  # 이메일 채널
        "name": "Email",
        "enabled": True,  # 활성화 상태
        "rate_limit": 100,  # 시간당 최대 전송 수
        "timeout_seconds": 30,  # 타임아웃(초)
        "retry_delays": [60, 300, 900],  # 재시도 대기 시간: 1분, 5분, 15분
        "max_content_length": 10000  # 최대 컨텐츠 길이
    },
    "slack": {  # Slack 채널
        "name": "Slack",
        "enabled": True,  # 활성화 상태
        "rate_limit": 200,  # 시간당 최대 전송 수
        "timeout_seconds": 15,  # 타임아웃(초)
        "retry_delays": [30, 180, 600],  # 재시도 대기 시간: 30초, 3분, 10분
        "max_content_length": 4000  # 최대 컨텐츠 길이
    },
    "webhook": {  # 웹훅 채널
        "name": "Webhook",
        "enabled": True,  # 활성화 상태
        "rate_limit": 500,  # 시간당 최대 전송 수
        "timeout_seconds": 30,  # 타임아웃(초)
        "retry_delays": [60, 300, 900],  # 재시도 대기 시간: 1분, 5분, 15분
        "max_content_length": 50000  # 최대 컨텐츠 길이
    },
    "sms": {  # SMS 채널
        "name": "SMS",
        "enabled": False,  # 활성화 상태 (기본값: 비활성)
        "rate_limit": 50,  # 시간당 최대 전송 수
        "timeout_seconds": 10,  # 타임아웃(초)
        "retry_delays": [120, 600, 1800],
        "max_content_length": 160
    }
}