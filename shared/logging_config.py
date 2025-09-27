"""
구조화 로깅 설정
JSON 형식, 요청 ID, 트레이스 ID 포함
작성일: 2025-09-26
"""

import logging
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import traceback

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar('span_id', default=None)


class StructuredFormatter(logging.Formatter):
    """구조화된 JSON 로그 포맷터"""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        super().__init__()
        self.service_name = service_name
        self.version = version
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 포맷"""
        
        # 기본 로그 필드
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "version": self.version,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Context 정보 추가
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        span_id = span_id_var.get()
        if span_id:
            log_data["span_id"] = span_id
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 추가 필드
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        # 성능 메트릭
        if hasattr(record, 'duration'):
            log_data["duration_ms"] = record.duration
        
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        
        if hasattr(record, 'path'):
            log_data["path"] = record.path
        
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        
        # JSON으로 변환
        return json.dumps(log_data, ensure_ascii=False, default=str)


class RequestContextMiddleware:
    """FastAPI용 요청 컨텍스트 미들웨어"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, request, call_next):
        """요청 처리 및 컨텍스트 설정"""
        import time
        from fastapi import Request, Response
        
        # 요청 ID 생성 또는 추출
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        span_id = str(uuid.uuid4())
        
        # Context 설정
        request_id_var.set(request_id)
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)
        
        # 시작 시간 기록
        start_time = time.time()
        
        # 요청 로깅
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.url.query),
                "client_host": request.client.host if request.client else None
            }
        )
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 헤더에 추가
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            
            # 처리 시간 계산
            duration = (time.time() - start_time) * 1000  # ms
            
            # 응답 로깅
            self.logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "duration_ms": duration
                }
            )
            
            return response
            
        except Exception as e:
            # 에러 로깅
            duration = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": duration,
                    "error": str(e)
                }
            )
            raise
        finally:
            # Context 정리
            request_id_var.set(None)
            trace_id_var.set(None)
            span_id_var.set(None)


def setup_logging(
    service_name: str, 
    version: str = "1.0.0",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> None:
    """로깅 설정 초기화"""
    
    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    # 구조화된 포맷터 생성
    formatter = StructuredFormatter(service_name, version)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 초기 로그
    root_logger.info(
        f"Logging initialized for {service_name}",
        extra={
            "service": service_name,
            "version": version,
            "log_level": level
        }
    )


class MetricsLogger:
    """메트릭 로깅 유틸리티"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.metrics")
    
    def log_request_metric(
        self, 
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """요청 메트릭 로깅"""
        metric_data = {
            "metric_type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "success": 200 <= status_code < 400
        }
        
        if error:
            metric_data["error"] = error
        
        self.logger.info("HTTP Request Metric", extra={"metrics": metric_data})
    
    def log_business_metric(
        self,
        metric_name: str,
        value: Any,
        tags: Optional[Dict[str, str]] = None
    ):
        """비즈니스 메트릭 로깅"""
        metric_data = {
            "metric_type": "business",
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {}
        }
        
        self.logger.info(f"Business Metric: {metric_name}", extra={"metrics": metric_data})
    
    def log_error_metric(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """에러 메트릭 로깅"""
        metric_data = {
            "metric_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self.logger.error(f"Error Metric: {error_type}", extra={"metrics": metric_data})
