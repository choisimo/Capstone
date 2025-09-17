import os
from dataclasses import dataclass
from typing import Optional

# Load .env for local development (best-effort)
try:
    from dotenv import load_dotenv  # type: ignore
    # Load from current working directory and module directory as fallback
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass


@dataclass
class ChangeDetectionConfig:
    base_url: str
    api_key: str

    @staticmethod
    def from_env() -> "ChangeDetectionConfig":
        base = os.getenv("CHANGEDETECTION_BASE_URL", "http://localhost:5000/api/v1")
        key = os.getenv("CHANGEDETECTION_API_KEY", "")
        return ChangeDetectionConfig(base_url=base.rstrip("/"), api_key=key)


@dataclass
class PerplexityConfig:
    base_url: str
    api_key: str
    model: str = "pplx-70b-online"
    timeout_sec: int = 30

    @staticmethod
    def from_env() -> "PerplexityConfig":
        base = os.getenv("PPLX_BASE_URL", "https://api.perplexity.ai")
        key = os.getenv("PPLX_API_KEY", "")
        model = os.getenv("PPLX_MODEL", "pplx-70b-online")
        timeout = int(os.getenv("PPLX_TIMEOUT_SEC", "30"))
        return PerplexityConfig(base_url=base.rstrip("/"), api_key=key, model=model, timeout_sec=timeout)


@dataclass
class BusConfig:
    bus: str  # "kafka" | "pubsub" | "stdout"
    raw_topic: str
    kafka_brokers: Optional[str] = None
    pubsub_project: Optional[str] = None

    @staticmethod
    def from_env() -> "BusConfig":
        bus_env = os.getenv("MESSAGE_BUS")
        kafka_brokers = os.getenv("KAFKA_BROKERS")
        pubsub_project = os.getenv("PUBSUB_PROJECT")

        if not bus_env or bus_env.lower() == "auto":
            if kafka_brokers:
                bus = "kafka"
            elif pubsub_project:
                bus = "pubsub"
            else:
                bus = "stdout"
        else:
            bus = bus_env.lower()

        # Ensure defaults for connection
        if bus == "kafka" and not kafka_brokers:
            kafka_brokers = "localhost:19092"

        # Topic mapping default by bus type
        if bus == "pubsub":
            topic = os.getenv("RAW_TOPIC", "raw-posts")
        else:
            topic = os.getenv("RAW_TOPIC", "raw.posts.v1")

        return BusConfig(
            bus=bus,
            raw_topic=topic,
            kafka_brokers=kafka_brokers,
            pubsub_project=pubsub_project,
        )


@dataclass
class BridgeConfig:
    poll_interval_sec: int = 60
    include_html: bool = False
    watch_tag: Optional[str] = None  # name (not uuid)
    source: str = "web"
    channel: str = "changedetection"
    platform_profile: str = "public-web"
    state_path: str = os.getenv("COLLECTOR_STATE_PATH", ".collector_state.json")

    @staticmethod
    def from_env() -> "BridgeConfig":
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
    port: int = 8001
    allow_execute_js: bool = False
    default_recheck_on_create: bool = False
    default_recheck_on_update: bool = False

    @staticmethod
    def from_env() -> "AgentConfig":
        return AgentConfig(
            port=int(os.getenv("AGENT_PORT", "8001")),
            allow_execute_js=os.getenv("AGENT_ALLOW_EXECUTE_JS", "0") in ("1", "true", "True"),
            default_recheck_on_create=os.getenv("AGENT_RECHECK_ON_CREATE", "0") in ("1", "true", "True"),
            default_recheck_on_update=os.getenv("AGENT_RECHECK_ON_UPDATE", "0") in ("1", "true", "True"),
        )
