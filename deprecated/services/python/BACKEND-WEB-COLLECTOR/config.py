"""
Collector Service 설정 모듈

웹 수집기의 각종 설정을 관리하는 모듈입니다.
ChangeDetection.io, Perplexity, 메시지 버스 등의 설정을 포함합니다.
"""

import os
from dataclasses import dataclass
from typing import Optional

# 로컬 개발을 위한 .env 파일 로드 (선택적)
try:
    from dotenv import load_dotenv  # type: ignore
    # 현재 디렉토리와 모듈 디렉토리에서 .env 파일 로드 시도
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass  # .env 파일이 없어도 계속 진행


@dataclass
class ChangeDetectionConfig:
    """
    ChangeDetection.io 설정 클래스
    
    웹페이지 변경 감지 서비스 연동을 위한 설정입니다.
    """
    base_url: str  # ChangeDetection.io API URL
    api_key: str  # API 인증 키

    @staticmethod
    def from_env() -> "ChangeDetectionConfig":
        """
        환경 변수에서 설정 로드
        
        Returns:
            ChangeDetectionConfig: 설정 인스턴스
        """
        base = os.getenv("CHANGEDETECTION_BASE_URL", "http://localhost:5000/api/v1")
        key = os.getenv("CHANGEDETECTION_API_KEY", "")
        return ChangeDetectionConfig(base_url=base.rstrip("/"), api_key=key)


@dataclass
class PerplexityConfig:
    """
    Perplexity AI 설정 클래스
    
    AI 기반 웹 검색 서비스 연동을 위한 설정입니다.
    """
    base_url: str  # Perplexity API URL
    api_key: str  # API 인증 키
    model: str = "pplx-70b-online"  # 사용할 모델 (온라인 검색 가능 모델)
    timeout_sec: int = 30  # API 요청 타임아웃 (초)

    @staticmethod
    def from_env() -> "PerplexityConfig":
        """
        환경 변수에서 설정 로드
        
        Returns:
            PerplexityConfig: 설정 인스턴스
        """
        base = os.getenv("PPLX_BASE_URL", "https://api.perplexity.ai")
        key = os.getenv("PPLX_API_KEY", "")
        model = os.getenv("PPLX_MODEL", "pplx-70b-online")
        timeout = int(os.getenv("PPLX_TIMEOUT_SEC", "30"))
        return PerplexityConfig(base_url=base.rstrip("/"), api_key=key, model=model, timeout_sec=timeout)


@dataclass
class BusConfig:
    """
    메시지 버스 설정 클래스
    
    이벤트 발행을 위한 메시지 버스 설정입니다.
    Kafka, Google Pub/Sub, stdout를 지원합니다.
    """
    bus: str  # 메시지 버스 타입 ("kafka" | "pubsub" | "stdout")
    raw_topic: str  # 원시 데이터 토픽명
    summary_topic: str  # 요약 데이터 토픽명
    kafka_brokers: Optional[str] = None  # Kafka 브로커 주소
    pubsub_project: Optional[str] = None  # Google Cloud 프로젝트 ID

    @staticmethod
    def from_env() -> "BusConfig":
        """
        환경 변수에서 설정 로드
        
        자동으로 사용 가능한 메시지 버스를 감지하여 설정합니다.
        
        Returns:
            BusConfig: 설정 인스턴스
        """
        bus_env = os.getenv("MESSAGE_BUS")
        kafka_brokers = os.getenv("KAFKA_BROKERS")
        pubsub_project = os.getenv("PUBSUB_PROJECT")

        # 메시지 버스 자동 감지
        if not bus_env or bus_env.lower() == "auto":
            if kafka_brokers:
                bus = "kafka"  # Kafka 브로커가 설정되어 있으면 Kafka 사용
            elif pubsub_project:
                bus = "pubsub"  # Pub/Sub 프로젝트가 설정되어 있으면 Pub/Sub 사용
            else:
                bus = "stdout"  # 둘 다 없으면 stdout으로 출력
        else:
            bus = bus_env.lower()

        # Kafka 기본 연결 설정
        if bus == "kafka" and not kafka_brokers:
            kafka_brokers = "localhost:19092"  # 기본 Kafka 브로커 주소

        # 버스 타입별 토픽명 기본값 설정
        if bus == "pubsub":
            # Google Pub/Sub은 하이픈 사용
            raw_topic = os.getenv("RAW_TOPIC", "raw-posts")
            summary_topic = os.getenv("SUMMARY_TOPIC", "summary-events")
        else:
            # Kafka는 점 표기법 사용
            raw_topic = os.getenv("RAW_TOPIC", "raw.posts.v1")
            summary_topic = os.getenv("SUMMARY_TOPIC", "summary.events.v1")

        return BusConfig(
            bus=bus,
            raw_topic=raw_topic,
            summary_topic=summary_topic,
            kafka_brokers=kafka_brokers,
            pubsub_project=pubsub_project,
        )


@dataclass
class BridgeConfig:
    """
    브릿지 설정 클래스
    
    ChangeDetection.io와 메시지 버스를 연결하는 브릿지 설정입니다.
    """
    poll_interval_sec: int = 60  # 폴링 간격 (초)
    include_html: bool = False  # HTML 포함 여부
    watch_tag: Optional[str] = None  # ChangeDetection.io 태그 이름 (UUID 아님)
    source: str = "web"  # 데이터 소스 타입
    channel: str = "changedetection"  # 채널 이름
    platform_profile: str = "public-web"  # 플랫폼 프로필
    state_path: str = os.getenv("COLLECTOR_STATE_PATH", ".collector_state.json")  # 상태 저장 파일 경로

    @staticmethod
    def from_env() -> "BridgeConfig":
        """
        환경 변수에서 설정 로드
        
        Returns:
            BridgeConfig: 설정 인스턴스
        """
        return BridgeConfig(
            poll_interval_sec=int(os.getenv("POLL_INTERVAL_SEC", "60")),
            include_html=os.getenv("INCLUDE_HTML", "0") in ("1", "true", "True"),
            watch_tag=os.getenv("WATCH_TAG"),
            source=os.getenv("SOURCE", "web"),
            channel=os.getenv("CHANNEL", "changedetection"),
            platform_profile=os.getenv("PLATFORM_PROFILE", "public-web"),
            state_path=os.getenv("COLLECTOR_STATE_PATH", ".collector_state.json"),
        )


@dataclass
class AgentConfig:
    """
    에이전트 서비스 설정 클래스
    
    웹 수집 에이전트 서버의 설정입니다.
    """
    port: int = 8001  # 서버 포트
    allow_execute_js: bool = False  # JavaScript 실행 허용 여부
    default_recheck_on_create: bool = False  # 생성 시 재확인 기본값
    default_recheck_on_update: bool = False  # 업데이트 시 재확인 기본값

    @staticmethod
    def from_env() -> "AgentConfig":
        """
        환경 변수에서 설정 로드
        
        Returns:
            AgentConfig: 설정 인스턴스
        """
        return AgentConfig(
            port=int(os.getenv("AGENT_PORT", "8001")),
            allow_execute_js=os.getenv("AGENT_ALLOW_EXECUTE_JS", "0") in ("1", "true", "True"),
            default_recheck_on_create=os.getenv("AGENT_RECHECK_ON_CREATE", "0") in ("1", "true", "True"),
            default_recheck_on_update=os.getenv("AGENT_RECHECK_ON_UPDATE", "0") in ("1", "true", "True"),
        )
