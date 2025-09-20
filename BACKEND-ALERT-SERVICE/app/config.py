"""
Alert Service 설정 모듈

알림 서비스의 모든 설정을 관리합니다.
데이터베이스, 알림 채널, 외부 서비스 연동 등의 설정을 포함합니다.
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    서비스 설정 클래스
    
    환경 변수에서 설정을 읽어오며, 기본값을 제공합니다.
    """
    
    # 데이터베이스 설정
    database_url: str = "postgresql://pension_user:pension_pass@localhost:5432/pension_sentiment"  # PostgreSQL URL
    
    # Redis 캐시 설정
    redis_url: str = "redis://localhost:6379"  # Redis 캐시 서버 URL
    
    # 서비스 기본 설정
    service_name: str = "alert-service"  # 서비스 이름
    service_version: str = "1.0.0"  # 서비스 버전
    debug: bool = False  # 디버그 모드
    
    # 외부 서비스 API 키
    email_service_api_key: str = ""  # 이메일 서비스 API 키
    slack_webhook_url: str = ""  # Slack 웹훅 URL
    slack_bot_token: str = ""  # Slack 봇 토큰
    twilio_account_sid: str = ""  # Twilio 계정 SID (SMS 전송)
    twilio_auth_token: str = ""  # Twilio 인증 토큰
    
    # SMTP 설정 (이메일 전송)
    smtp_server: str = "smtp.gmail.com"  # SMTP 서버 주소
    smtp_port: int = 587  # SMTP 포트 (TLS)
    smtp_username: str = ""  # SMTP 사용자명
    smtp_password: str = ""  # SMTP 비밀번호
    from_email: str = "alerts@pensionsentiment.com"  # 발신자 이메일
    
    # 알림 설정
    max_retries: int = 3  # 최대 재시도 횟수
    retry_delay_seconds: int = 300  # 재시도 대기 시간 (300초 = 5분)
    batch_size: int = 100  # 배치 처리 크기
    rate_limit_per_minute: int = 60  # 분당 최대 알림 수
    
    # 알림 임계값 및 제한
    max_alerts_per_hour: int = 1000  # 시간당 최대 알림 수
    cooldown_override_enabled: bool = False  # 쿨다운 무시 설정
    
    # 알림 채널
    enabled_channels: List[str] = ["email", "slack", "webhook"]  # 활성화된 알림 채널
    
    # 웹훅 설정
    webhook_timeout_seconds: int = 30  # 웹훅 타임아웃 (초)
    webhook_retry_attempts: int = 3  # 웹훅 재시도 횟수
    
    # 보안 설정
    api_key_header: str = "X-API-Key"  # API 키 헤더 이름
    allowed_origins: List[str] = ["*"]  # CORS 허용 도메인
    
    # 모니터링 및 로깅
    log_level: str = "INFO"  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    enable_metrics: bool = True  # 메트릭 활성화
    metrics_port: int = 9090  # Prometheus 메트릭 포트
    
    # 외부 서비스 URL
    analysis_service_url: str = "http://localhost:8001"  # 분석 서비스 URL
    collector_service_url: str = "http://localhost:8002"  # 수집 서비스 URL
    absa_service_url: str = "http://localhost:8003"  # ABSA 서비스 URL
    
    # 템플릿 설정
    default_email_template: str = """  # 기본 이메일 템플릿 (HTML 형식)
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
    
    default_slack_template: str = """  # 기본 Slack 템플릿 (Markdown 형식)
    :warning: *{{alert_title}}*
    
    *심각도:* {{severity}}
    *서비스:* {{source_service}}
    *시간:* {{triggered_at}}
    
    {{message}}
    
    {% if actual_value and threshold_value %}
    *현재 값:* {{actual_value}} (임계값: {{threshold_value}})
    {% endif %}
    """
    
    # 방해 금지 시간 설정 (알림을 제한해야 하는 시간)
    quiet_hours_enabled: bool = True  # 방해 금지 시간 활성화
    quiet_hours_start: str = "22:00"  # 방해 금지 시작 시간
    quiet_hours_end: str = "08:00"  # 방해 금지 종료 시간
    quiet_hours_timezone: str = "UTC"  # 방해 금지 시간대
    
    # 방해 금지 시간에는 중요 알림만 전송
    quiet_hours_critical_only: bool = True  # 중요 알림만 허용
    
    class Config:
        """
        설정 클래스 메타데이터
        """
        env_file = ".env"  # 환경 변수 파일
        case_sensitive = False  # 대소문자 구분 안함

# 전역 설정 인스턴스
settings = Settings()

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