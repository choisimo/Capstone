"""
대시보드 설정
Grafana 대시보드 생성 및 설정
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardConfig:
    """대시보드 설정"""
    
    def __init__(
        self,
        title: str = "Hybrid Crawler Monitoring",
        uid: str = "hybrid-crawler",
        refresh: str = "5s",
        timezone: str = "browser"
    ):
        """
        초기화
        
        Args:
            title: 대시보드 제목
            uid: 대시보드 UID
            refresh: 새로고침 간격
            timezone: 시간대
        """
        self.title = title
        self.uid = uid
        self.refresh = refresh
        self.timezone = timezone
        self.panels = []
        self.templating = []
        self.annotations = []
    
    def add_panel(self, panel: Dict[str, Any]):
        """패널 추가"""
        panel["id"] = len(self.panels) + 1
        self.panels.append(panel)
    
    def to_json(self) -> Dict[str, Any]:
        """JSON 변환"""
        return {
            "dashboard": {
                "id": None,
                "uid": self.uid,
                "title": self.title,
                "tags": ["hybrid-crawler", "monitoring"],
                "timezone": self.timezone,
                "schemaVersion": 27,
                "version": 0,
                "refresh": self.refresh,
                "panels": self.panels,
                "templating": {"list": self.templating},
                "annotations": {"list": self.annotations},
                "time": {
                    "from": "now-6h",
                    "to": "now"
                }
            },
            "overwrite": True
        }


def create_grafana_dashboard() -> DashboardConfig:
    """Grafana 대시보드 생성"""
    dashboard = DashboardConfig()
    
    # Row 1: 시스템 상태
    dashboard.add_panel({
        "type": "stat",
        "title": "System Status",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "targets": [{
            "expr": "up{job='hybrid-crawler'}",
            "legendFormat": "Status"
        }],
        "fieldConfig": {
            "defaults": {
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": 0},
                        {"color": "green", "value": 1}
                    ]
                },
                "mappings": [{
                    "type": "value",
                    "options": {
                        "0": {"text": "Down", "color": "red"},
                        "1": {"text": "Up", "color": "green"}
                    }
                }]
            }
        }
    })
    
    dashboard.add_panel({
        "type": "stat",
        "title": "Uptime",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
        "targets": [{
            "expr": "system_uptime_seconds",
            "legendFormat": "Uptime"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "s",
                "decimals": 0
            }
        }
    })
    
    dashboard.add_panel({
        "type": "gauge",
        "title": "CPU Usage",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
        "targets": [{
            "expr": "system_cpu_usage_percent",
            "legendFormat": "CPU"
        }],
        "fieldConfig": {
            "defaults": {
                "min": 0,
                "max": 100,
                "unit": "percent",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 60},
                        {"color": "red", "value": 80}
                    ]
                }
            }
        }
    })
    
    dashboard.add_panel({
        "type": "gauge",
        "title": "Memory Usage",
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
        "targets": [{
            "expr": "system_memory_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "Memory"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "GB",
                "decimals": 2,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 4},
                        {"color": "red", "value": 6}
                    ]
                }
            }
        }
    })
    
    # Row 2: API 메트릭
    dashboard.add_panel({
        "type": "graph",
        "title": "Request Rate",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
        "targets": [{
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}} {{status}}"
        }],
        "yaxes": [
            {"format": "reqps", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    dashboard.add_panel({
        "type": "graph",
        "title": "Request Duration",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
        "targets": [{
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95 {{method}} {{endpoint}}"
        }, {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p50 {{method}} {{endpoint}}"
        }],
        "yaxes": [
            {"format": "s", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    # Row 3: 작업 메트릭
    dashboard.add_panel({
        "type": "stat",
        "title": "Active Tasks",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 12},
        "targets": [{
            "expr": "sum(tasks_active)",
            "legendFormat": "Active"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "short",
                "decimals": 0,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 50},
                        {"color": "red", "value": 100}
                    ]
                }
            }
        }
    })
    
    dashboard.add_panel({
        "type": "graph",
        "title": "Task Processing Rate",
        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 12},
        "targets": [{
            "expr": "rate(tasks_total[5m])",
            "legendFormat": "{{type}} {{status}}"
        }],
        "yaxes": [
            {"format": "ops", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    # Row 4: 스크래핑 메트릭
    dashboard.add_panel({
        "type": "piechart",
        "title": "Scraping Success Rate",
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 20},
        "targets": [{
            "expr": "sum(rate(scraping_requests_total{status='success'}[5m]))",
            "legendFormat": "Success"
        }, {
            "expr": "sum(rate(scraping_requests_total{status='failed'}[5m]))",
            "legendFormat": "Failed"
        }],
        "pieType": "pie",
        "legendDisplayMode": "list",
        "legendPlacement": "right"
    })
    
    dashboard.add_panel({
        "type": "graph",
        "title": "Scraping Duration by Strategy",
        "gridPos": {"h": 8, "w": 16, "x": 8, "y": 20},
        "targets": [{
            "expr": "histogram_quantile(0.95, rate(scraping_duration_seconds_bucket[5m]))",
            "legendFormat": "p95 {{strategy}}"
        }, {
            "expr": "histogram_quantile(0.50, rate(scraping_duration_seconds_bucket[5m]))",
            "legendFormat": "p50 {{strategy}}"
        }],
        "yaxes": [
            {"format": "s", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    # Row 5: 분석 메트릭
    dashboard.add_panel({
        "type": "graph",
        "title": "Analysis Request Rate",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 28},
        "targets": [{
            "expr": "rate(analysis_requests_total[5m])",
            "legendFormat": "{{type}} {{status}}"
        }],
        "yaxes": [
            {"format": "reqps", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    dashboard.add_panel({
        "type": "heatmap",
        "title": "Analysis Duration Heatmap",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 28},
        "targets": [{
            "expr": "rate(analysis_duration_seconds_bucket[5m])",
            "format": "heatmap",
            "legendFormat": "{{le}}"
        }],
        "dataFormat": "tsbuckets",
        "yAxis": {"format": "s"},
        "cards": {"cardPadding": 2, "cardRound": 2}
    })
    
    # Row 6: 캐시 메트릭
    dashboard.add_panel({
        "type": "stat",
        "title": "Cache Hit Rate",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 36},
        "targets": [{
            "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100",
            "legendFormat": "Hit Rate"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "decimals": 1,
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": 0},
                        {"color": "yellow", "value": 50},
                        {"color": "green", "value": 80}
                    ]
                }
            }
        }
    })
    
    dashboard.add_panel({
        "type": "stat",
        "title": "Cache Size",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 36},
        "targets": [{
            "expr": "cache_size_bytes / 1024 / 1024",
            "legendFormat": "Size"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "MB",
                "decimals": 2
            }
        }
    })
    
    dashboard.add_panel({
        "type": "graph",
        "title": "Cache Operations",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 36},
        "targets": [{
            "expr": "rate(cache_hits_total[5m])",
            "legendFormat": "Hits"
        }, {
            "expr": "rate(cache_misses_total[5m])",
            "legendFormat": "Misses"
        }],
        "yaxes": [
            {"format": "ops", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    # Row 7: 데이터베이스 메트릭
    dashboard.add_panel({
        "type": "stat",
        "title": "DB Connections",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 44},
        "targets": [{
            "expr": "db_connections_active",
            "legendFormat": "Active"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "short",
                "decimals": 0,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 20},
                        {"color": "red", "value": 40}
                    ]
                }
            }
        }
    })
    
    dashboard.add_panel({
        "type": "graph",
        "title": "Database Query Rate",
        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 44},
        "targets": [{
            "expr": "rate(db_queries_total[5m])",
            "legendFormat": "{{operation}}"
        }],
        "yaxes": [
            {"format": "qps", "show": True},
            {"format": "short", "show": False}
        ],
        "xaxis": {"show": True}
    })
    
    # Variables
    dashboard.templating = [
        {
            "name": "interval",
            "type": "interval",
            "current": {"text": "5m", "value": "5m"},
            "hide": 0,
            "label": "Interval",
            "options": [
                {"text": "1m", "value": "1m"},
                {"text": "5m", "value": "5m"},
                {"text": "10m", "value": "10m"},
                {"text": "30m", "value": "30m"},
                {"text": "1h", "value": "1h"}
            ],
            "query": "1m,5m,10m,30m,1h",
            "refresh": 2
        }
    ]
    
    # Annotations
    dashboard.annotations = [
        {
            "name": "Deployments",
            "datasource": "Prometheus",
            "enable": True,
            "hide": False,
            "iconColor": "rgba(0, 211, 255, 1)",
            "query": "deployment_info",
            "tagKeys": "version,service",
            "textFormat": "Deployed {{version}}"
        }
    ]
    
    return dashboard


def export_dashboard_json(
    dashboard: DashboardConfig,
    filename: str = "hybrid_crawler_dashboard.json"
):
    """
    대시보드 JSON 파일로 내보내기
    
    Args:
        dashboard: 대시보드 설정
        filename: 파일명
    """
    try:
        with open(filename, "w") as f:
            json.dump(dashboard.to_json(), f, indent=2)
        logger.info(f"Dashboard exported to {filename}")
    except Exception as e:
        logger.error(f"Failed to export dashboard: {e}")


def create_alert_rules() -> List[Dict[str, Any]]:
    """알림 규칙 생성"""
    rules = []
    
    # CPU 알림
    rules.append({
        "alert": "HighCPUUsage",
        "expr": "system_cpu_usage_percent > 80",
        "for": "5m",
        "annotations": {
            "summary": "High CPU usage detected",
            "description": "CPU usage is above 80% for more than 5 minutes"
        },
        "labels": {
            "severity": "warning",
            "service": "hybrid-crawler"
        }
    })
    
    # 메모리 알림
    rules.append({
        "alert": "HighMemoryUsage",
        "expr": "(system_memory_usage_bytes / system_memory_total_bytes) * 100 > 90",
        "for": "5m",
        "annotations": {
            "summary": "High memory usage detected",
            "description": "Memory usage is above 90% for more than 5 minutes"
        },
        "labels": {
            "severity": "critical",
            "service": "hybrid-crawler"
        }
    })
    
    # API 에러율 알림
    rules.append({
        "alert": "HighAPIErrorRate",
        "expr": "rate(http_requests_total{status=~'5..'}[5m]) > 0.05",
        "for": "5m",
        "annotations": {
            "summary": "High API error rate",
            "description": "API error rate is above 5% for more than 5 minutes"
        },
        "labels": {
            "severity": "warning",
            "service": "hybrid-crawler"
        }
    })
    
    # 작업 실패율 알림
    rules.append({
        "alert": "HighTaskFailureRate",
        "expr": "rate(tasks_total{status='failed'}[5m]) > rate(tasks_total{status='completed'}[5m])",
        "for": "10m",
        "annotations": {
            "summary": "High task failure rate",
            "description": "Task failure rate is higher than success rate"
        },
        "labels": {
            "severity": "critical",
            "service": "hybrid-crawler"
        }
    })
    
    # 캐시 히트율 알림
    rules.append({
        "alert": "LowCacheHitRate",
        "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) < 0.5",
        "for": "15m",
        "annotations": {
            "summary": "Low cache hit rate",
            "description": "Cache hit rate is below 50% for more than 15 minutes"
        },
        "labels": {
            "severity": "info",
            "service": "hybrid-crawler"
        }
    })
    
    # DB 연결 알림
    rules.append({
        "alert": "HighDatabaseConnections",
        "expr": "db_connections_active > 40",
        "for": "5m",
        "annotations": {
            "summary": "High database connections",
            "description": "Database connections exceed 40 for more than 5 minutes"
        },
        "labels": {
            "severity": "warning",
            "service": "hybrid-crawler"
        }
    })
    
    return rules
