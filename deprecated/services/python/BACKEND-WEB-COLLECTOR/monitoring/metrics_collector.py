"""
메트릭 수집기
Prometheus 메트릭 수집
"""
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import asyncio
from collections import defaultdict
import statistics

try:
    from prometheus_client import (
        Counter as PrometheusCounter,
        Gauge as PrometheusGauge,
        Histogram as PrometheusHistogram,
        Summary as PrometheusSummary,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricBase:
    """메트릭 베이스 클래스"""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values = defaultdict(float)
        self.timestamps = defaultdict(float)


class Counter(MetricBase):
    """카운터 메트릭"""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        super().__init__(name, description, labels)
        
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metric = PrometheusCounter(
                name, description, labels
            )
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None):
        """값 증가"""
        label_key = self._get_label_key(labels)
        self.values[label_key] += value
        self.timestamps[label_key] = time.time()
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).inc(value)
            else:
                self.prometheus_metric.inc(value)
    
    def _get_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """레이블 키 생성"""
        if not labels:
            return "default"
        return ":".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Gauge(MetricBase):
    """게이지 메트릭"""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        super().__init__(name, description, labels)
        
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metric = PrometheusGauge(
                name, description, labels
            )
    
    def set(self, value: float, labels: Dict[str, str] = None):
        """값 설정"""
        label_key = self._get_label_key(labels)
        self.values[label_key] = value
        self.timestamps[label_key] = time.time()
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).set(value)
            else:
                self.prometheus_metric.set(value)
    
    def inc(self, value: float = 1, labels: Dict[str, str] = None):
        """값 증가"""
        label_key = self._get_label_key(labels)
        self.values[label_key] += value
        self.timestamps[label_key] = time.time()
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).inc(value)
            else:
                self.prometheus_metric.inc(value)
    
    def dec(self, value: float = 1, labels: Dict[str, str] = None):
        """값 감소"""
        label_key = self._get_label_key(labels)
        self.values[label_key] -= value
        self.timestamps[label_key] = time.time()
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).dec(value)
            else:
                self.prometheus_metric.dec(value)
    
    def _get_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """레이블 키 생성"""
        if not labels:
            return "default"
        return ":".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Histogram(MetricBase):
    """히스토그램 메트릭"""
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        buckets: List[float] = None
    ):
        super().__init__(name, description, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self.observations = defaultdict(list)
        
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metric = PrometheusHistogram(
                name, description, labels, buckets=self.buckets
            )
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """값 관찰"""
        label_key = self._get_label_key(labels)
        self.observations[label_key].append(value)
        self.timestamps[label_key] = time.time()
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).observe(value)
            else:
                self.prometheus_metric.observe(value)
    
    def get_stats(self, labels: Dict[str, str] = None) -> Dict[str, float]:
        """통계 반환"""
        label_key = self._get_label_key(labels)
        obs = self.observations.get(label_key, [])
        
        if not obs:
            return {}
        
        return {
            "count": len(obs),
            "sum": sum(obs),
            "mean": statistics.mean(obs),
            "median": statistics.median(obs),
            "min": min(obs),
            "max": max(obs),
            "stddev": statistics.stdev(obs) if len(obs) > 1 else 0
        }
    
    def _get_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """레이블 키 생성"""
        if not labels:
            return "default"
        return ":".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Summary(MetricBase):
    """요약 메트릭"""
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        max_age: int = 600
    ):
        super().__init__(name, description, labels)
        self.max_age = max_age
        self.observations = defaultdict(list)
        
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metric = PrometheusSummary(
                name, description, labels
            )
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """값 관찰"""
        label_key = self._get_label_key(labels)
        now = time.time()
        
        # 오래된 관찰값 제거
        self.observations[label_key] = [
            (t, v) for t, v in self.observations[label_key]
            if now - t < self.max_age
        ]
        
        # 새 관찰값 추가
        self.observations[label_key].append((now, value))
        self.timestamps[label_key] = now
        
        if PROMETHEUS_AVAILABLE and self.prometheus_metric:
            if labels:
                self.prometheus_metric.labels(**labels).observe(value)
            else:
                self.prometheus_metric.observe(value)
    
    def _get_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """레이블 키 생성"""
        if not labels:
            return "default"
        return ":".join(f"{k}={v}" for k, v in sorted(labels.items()))


class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        """초기화"""
        self.metrics: Dict[str, MetricBase] = {}
        
        # 기본 메트릭 생성
        self._create_default_metrics()
        
        # 수집 태스크
        self.collection_task = None
        self.collection_interval = 10  # 10초
        
        logger.info("Metrics collector initialized")
    
    def _create_default_metrics(self):
        """기본 메트릭 생성"""
        # 요청 메트릭
        self.metrics["http_requests_total"] = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        
        self.metrics["http_request_duration_seconds"] = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"]
        )
        
        # 작업 메트릭
        self.metrics["tasks_total"] = Counter(
            "tasks_total",
            "Total tasks",
            ["type", "status"]
        )
        
        self.metrics["tasks_duration_seconds"] = Histogram(
            "tasks_duration_seconds",
            "Task duration",
            ["type"]
        )
        
        self.metrics["tasks_active"] = Gauge(
            "tasks_active",
            "Active tasks",
            ["type"]
        )
        
        # 스크래핑 메트릭
        self.metrics["scraping_requests_total"] = Counter(
            "scraping_requests_total",
            "Total scraping requests",
            ["strategy", "status"]
        )
        
        self.metrics["scraping_duration_seconds"] = Histogram(
            "scraping_duration_seconds",
            "Scraping duration",
            ["strategy"]
        )
        
        # 분석 메트릭
        self.metrics["analysis_requests_total"] = Counter(
            "analysis_requests_total",
            "Total analysis requests",
            ["type", "status"]
        )
        
        self.metrics["analysis_duration_seconds"] = Histogram(
            "analysis_duration_seconds",
            "Analysis duration",
            ["type"]
        )
        
        # 캐시 메트릭
        self.metrics["cache_hits_total"] = Counter(
            "cache_hits_total",
            "Total cache hits"
        )
        
        self.metrics["cache_misses_total"] = Counter(
            "cache_misses_total",
            "Total cache misses"
        )
        
        self.metrics["cache_size_bytes"] = Gauge(
            "cache_size_bytes",
            "Cache size in bytes"
        )
        
        # 데이터베이스 메트릭
        self.metrics["db_connections_active"] = Gauge(
            "db_connections_active",
            "Active database connections"
        )
        
        self.metrics["db_queries_total"] = Counter(
            "db_queries_total",
            "Total database queries",
            ["operation"]
        )
        
        self.metrics["db_query_duration_seconds"] = Histogram(
            "db_query_duration_seconds",
            "Database query duration",
            ["operation"]
        )
        
        # 시스템 메트릭
        self.metrics["system_cpu_usage_percent"] = Gauge(
            "system_cpu_usage_percent",
            "CPU usage percentage"
        )
        
        self.metrics["system_memory_usage_bytes"] = Gauge(
            "system_memory_usage_bytes",
            "Memory usage in bytes"
        )
        
        self.metrics["system_uptime_seconds"] = Gauge(
            "system_uptime_seconds",
            "System uptime in seconds"
        )
    
    def register_metric(self, metric: MetricBase):
        """메트릭 등록"""
        self.metrics[metric.name] = metric
    
    def get_metric(self, name: str) -> Optional[MetricBase]:
        """메트릭 조회"""
        return self.metrics.get(name)
    
    def counter(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None
    ) -> Counter:
        """카운터 생성"""
        if name not in self.metrics:
            metric = Counter(name, description, labels)
            self.register_metric(metric)
        return self.metrics[name]
    
    def gauge(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None
    ) -> Gauge:
        """게이지 생성"""
        if name not in self.metrics:
            metric = Gauge(name, description, labels)
            self.register_metric(metric)
        return self.metrics[name]
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: List[float] = None
    ) -> Histogram:
        """히스토그램 생성"""
        if name not in self.metrics:
            metric = Histogram(name, description, labels, buckets)
            self.register_metric(metric)
        return self.metrics[name]
    
    def summary(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None
    ) -> Summary:
        """요약 생성"""
        if name not in self.metrics:
            metric = Summary(name, description, labels)
            self.register_metric(metric)
        return self.metrics[name]
    
    async def start_collection(self):
        """수집 시작"""
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """수집 중지"""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.collection_task = None
        logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """수집 루프"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            import psutil
            
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            self.gauge("system_cpu_usage_percent").set(cpu_percent)
            
            # 메모리 사용량
            memory = psutil.virtual_memory()
            self.gauge("system_memory_usage_bytes").set(memory.used)
            
            # 프로세스 정보
            process = psutil.Process()
            self.gauge("process_cpu_percent").set(process.cpu_percent())
            self.gauge("process_memory_bytes").set(process.memory_info().rss)
            
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
    
    def get_prometheus_metrics(self) -> bytes:
        """Prometheus 형식 메트릭 반환"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(REGISTRY)
        return b""
    
    def get_json_metrics(self) -> Dict[str, Any]:
        """JSON 형식 메트릭 반환"""
        result = {}
        
        for name, metric in self.metrics.items():
            if isinstance(metric, (Counter, Gauge)):
                result[name] = dict(metric.values)
            elif isinstance(metric, Histogram):
                result[name] = {
                    label: metric.get_stats(
                        self._parse_label_key(label) if label != "default" else None
                    )
                    for label in metric.observations.keys()
                }
        
        return result
    
    def _parse_label_key(self, label_key: str) -> Dict[str, str]:
        """레이블 키 파싱"""
        if label_key == "default":
            return {}
        
        labels = {}
        for part in label_key.split(":"):
            if "=" in part:
                k, v = part.split("=", 1)
                labels[k] = v
        return labels


# 글로벌 메트릭 수집기
_metrics_collector: Optional[MetricsCollector] = None


def init_metrics() -> MetricsCollector:
    """메트릭 초기화"""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector


def get_metrics() -> Optional[MetricsCollector]:
    """메트릭 수집기 반환"""
    return _metrics_collector
