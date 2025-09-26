"""
표준 헬스체크 엔드포인트 구현
Liveness, Readiness, Metrics 제공
작성일: 2025-09-26
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckConfig:
    """헬스체크 설정"""
    service_name: str
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    custom_checks: List[Callable] = field(default_factory=list)


class HealthStatus:
    """헬스 상태"""
    def __init__(self, is_healthy: bool, message: str = "", details: Optional[Dict] = None):
        self.is_healthy = is_healthy
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class StandardHealthCheck:
    """표준 헬스체크 구현"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def get_liveness(self) -> HealthStatus:
        """
        Liveness 체크 - 프로세스/스레드 생존 확인
        기본 의존성 제외, 프로세스 자체의 건강 상태만 확인
        """
        try:
            # CPU 사용률 확인
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 메모리 사용률 확인
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 프로세스 정보
            process = psutil.Process()
            threads = process.num_threads()
            
            is_healthy = cpu_percent < 90 and memory_percent < 90
            
            return HealthStatus(
                is_healthy=is_healthy,
                message="Service is alive" if is_healthy else "Resource usage high",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "threads": threads,
                    "uptime": time.time() - self.start_time
                }
            )
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return HealthStatus(
                is_healthy=False,
                message=f"Liveness check error: {str(e)}"
            )
    
    async def get_readiness(self) -> HealthStatus:
        """
        Readiness 체크 - 의존성 포함한 준비 상태 확인
        DB, 캐시, 필수 서비스 연결 확인
        """
        checks_passed = []
        checks_failed = []
        details = {}
        
        # 기본 의존성 체크
        for dependency in self.config.dependencies:
            try:
                # 의존성별 체크 로직 (예시)
                if await self._check_dependency(dependency):
                    checks_passed.append(dependency)
                    details[dependency] = "healthy"
                else:
                    checks_failed.append(dependency)
                    details[dependency] = "unhealthy"
            except Exception as e:
                checks_failed.append(dependency)
                details[dependency] = f"error: {str(e)}"
        
        # 커스텀 체크
        for check_func in self.config.custom_checks:
            try:
                check_name = check_func.__name__
                if await check_func():
                    checks_passed.append(check_name)
                    details[check_name] = "passed"
                else:
                    checks_failed.append(check_name)
                    details[check_name] = "failed"
            except Exception as e:
                checks_failed.append(check_func.__name__)
                details[check_func.__name__] = f"error: {str(e)}"
        
        is_ready = len(checks_failed) == 0
        
        return HealthStatus(
            is_healthy=is_ready,
            message="Service is ready" if is_ready else f"Dependencies unhealthy: {', '.join(checks_failed)}",
            details={
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
                "dependency_status": details
            }
        )
    
    async def _check_dependency(self, dependency: str) -> bool:
        """의존성 체크 (구현 필요)"""
        # 실제 구현 시 각 의존성에 맞는 체크 로직 추가
        # 예: PostgreSQL, Redis, MongoDB 등
        if "postgres" in dependency.lower():
            return await self._check_postgres()
        elif "redis" in dependency.lower():
            return await self._check_redis()
        elif "mongo" in dependency.lower():
            return await self._check_mongodb()
        return True
    
    async def _check_postgres(self) -> bool:
        """PostgreSQL 연결 확인"""
        # 실제 구현 필요
        return True
    
    async def _check_redis(self) -> bool:
        """Redis 연결 확인"""
        # 실제 구현 필요
        return True
    
    async def _check_mongodb(self) -> bool:
        """MongoDB 연결 확인"""
        # 실제 구현 필요
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 정보 반환 (Prometheus 형식 호환)"""
        uptime = time.time() - self.start_time
        
        # 시스템 메트릭
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 프로세스 메트릭
        process = psutil.Process()
        
        return {
            # 서비스 메타데이터
            "service_name": self.config.service_name,
            "version": self.config.version,
            
            # 요청 메트릭
            "request_count_total": self.request_count,
            "error_count_total": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            
            # 시스템 메트릭
            "uptime_seconds": uptime,
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_bytes": memory.available,
            "disk_usage_percent": disk.percent,
            
            # 프로세스 메트릭
            "process_cpu_percent": process.cpu_percent(),
            "process_memory_mb": process.memory_info().rss / 1024 / 1024,
            "process_threads": process.num_threads(),
            "process_open_files": len(process.open_files()),
            
            # 타임스탬프
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def increment_request_count(self):
        """요청 카운트 증가"""
        self.request_count += 1
    
    def increment_error_count(self):
        """에러 카운트 증가"""
        self.error_count += 1


def setup_health_endpoints(app: FastAPI, health_check: StandardHealthCheck):
    """FastAPI 앱에 표준 헬스 엔드포인트 추가"""
    
    @app.get("/health", status_code=status.HTTP_200_OK)
    def liveness():
        """Liveness 프로브"""
        health_status = health_check.get_liveness()
        
        if health_status.is_healthy:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "healthy",
                    "message": health_status.message,
                    "timestamp": health_status.timestamp,
                    "details": health_status.details
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "message": health_status.message,
                    "timestamp": health_status.timestamp,
                    "details": health_status.details
                }
            )
    
    @app.get("/ready", status_code=status.HTTP_200_OK)
    async def readiness():
        """Readiness 프로브"""
        health_status = await health_check.get_readiness()
        
        if health_status.is_healthy:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ready",
                    "message": health_status.message,
                    "timestamp": health_status.timestamp,
                    "details": health_status.details
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "message": health_status.message,
                    "timestamp": health_status.timestamp,
                    "details": health_status.details
                }
            )
    
    @app.get("/metrics", status_code=status.HTTP_200_OK)
    def metrics():
        """메트릭 엔드포인트"""
        return health_check.get_metrics()
    
    # 미들웨어로 요청/에러 카운트 추적
    @app.middleware("http")
    async def track_requests(request, call_next):
        health_check.increment_request_count()
        
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                health_check.increment_error_count()
            return response
        except Exception as e:
            health_check.increment_error_count()
            raise e


# Graceful Shutdown 헬퍼
class GracefulShutdown:
    """우아한 종료 처리"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.shutdown_event = asyncio.Event()
        self.tasks: List[asyncio.Task] = []
        
    async def shutdown(self):
        """종료 처리"""
        logger.info(f"Graceful shutdown initiated, waiting up to {self.timeout} seconds...")
        
        # 종료 이벤트 설정
        self.shutdown_event.set()
        
        # 진행 중인 태스크 완료 대기
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks, return_exceptions=True),
                    timeout=self.timeout
                )
                logger.info("All tasks completed successfully")
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete within timeout")
                
                # 강제 취소
                for task in self.tasks:
                    if not task.done():
                        task.cancel()
                
                await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Graceful shutdown completed")
    
    def register_task(self, task: asyncio.Task):
        """태스크 등록"""
        self.tasks.append(task)
    
    def unregister_task(self, task: asyncio.Task):
        """태스크 해제"""
        if task in self.tasks:
            self.tasks.remove(task)
