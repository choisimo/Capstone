"""
헬스 체크
시스템 및 컴포넌트 상태 확인
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """헬스 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """컴포넌트 헬스 정보"""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        message: str = "",
        details: Dict[str, Any] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.checked_at = datetime.utcnow()
        self.response_time = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "response_time_ms": self.response_time * 1000
        }


class SystemHealth:
    """시스템 헬스 정보"""
    
    def __init__(self):
        self.status = HealthStatus.HEALTHY
        self.components: Dict[str, ComponentHealth] = {}
        self.checked_at = datetime.utcnow()
        self.uptime = 0.0
        
    def add_component(self, component: ComponentHealth):
        """컴포넌트 추가"""
        self.components[component.name] = component
        
        # 전체 상태 업데이트
        if component.status == HealthStatus.UNHEALTHY:
            self.status = HealthStatus.UNHEALTHY
        elif component.status == HealthStatus.DEGRADED and self.status != HealthStatus.UNHEALTHY:
            self.status = HealthStatus.DEGRADED
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "status": self.status,
            "checked_at": self.checked_at.isoformat(),
            "uptime_seconds": self.uptime,
            "components": {
                name: comp.to_dict()
                for name, comp in self.components.items()
            }
        }


class HealthChecker:
    """헬스 체커"""
    
    def __init__(self, check_interval: int = 30):
        """
        초기화
        
        Args:
            check_interval: 체크 간격 (초)
        """
        self.check_interval = check_interval
        self.checks: Dict[str, Callable] = {}
        self.last_check: Optional[SystemHealth] = None
        self.start_time = datetime.utcnow()
        self.check_task = None
        
        # 기본 체크 등록
        self._register_default_checks()
        
        logger.info("Health checker initialized")
    
    def _register_default_checks(self):
        """기본 체크 등록"""
        # 데이터베이스 체크
        self.register_check("database", self._check_database)
        
        # Redis 체크
        self.register_check("redis", self._check_redis)
        
        # Kafka 체크
        self.register_check("kafka", self._check_kafka)
        
        # API 체크
        self.register_check("api", self._check_api)
        
        # 디스크 체크
        self.register_check("disk", self._check_disk_space)
        
        # 메모리 체크
        self.register_check("memory", self._check_memory)
    
    def register_check(
        self,
        name: str,
        check_func: Callable
    ):
        """
        헬스 체크 등록
        
        Args:
            name: 체크 이름
            check_func: 체크 함수
        """
        self.checks[name] = check_func
        logger.info(f"Health check registered: {name}")
    
    async def check_health(self) -> SystemHealth:
        """헬스 체크 실행"""
        system_health = SystemHealth()
        system_health.uptime = (
            datetime.utcnow() - self.start_time
        ).total_seconds()
        
        # 모든 체크 실행
        tasks = []
        for name, check_func in self.checks.items():
            tasks.append(self._run_check(name, check_func))
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        for result in results:
            if isinstance(result, ComponentHealth):
                system_health.add_component(result)
            elif isinstance(result, Exception):
                logger.error(f"Health check error: {result}")
                system_health.add_component(
                    ComponentHealth(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=str(result)
                    )
                )
        
        self.last_check = system_health
        return system_health
    
    async def _run_check(
        self,
        name: str,
        check_func: Callable
    ) -> ComponentHealth:
        """체크 실행"""
        import time
        
        start_time = time.time()
        
        try:
            # 체크 함수 실행
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            # ComponentHealth 반환이 아닌 경우 변환
            if not isinstance(result, ComponentHealth):
                if isinstance(result, bool):
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    result = ComponentHealth(name=name, status=status)
                elif isinstance(result, dict):
                    result = ComponentHealth(
                        name=name,
                        status=result.get("status", HealthStatus.HEALTHY),
                        message=result.get("message", ""),
                        details=result.get("details", {})
                    )
                else:
                    result = ComponentHealth(name=name)
            
            result.response_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                details={"error": str(e)}
            )
    
    async def _check_database(self) -> ComponentHealth:
        """데이터베이스 체크"""
        try:
            from ..database.database import get_db
            
            # 간단한 쿼리 실행
            db = next(get_db())
            try:
                result = db.execute("SELECT 1")
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful"
                )
            finally:
                db.close()
                
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}"
            )
    
    async def _check_redis(self) -> ComponentHealth:
        """Redis 체크"""
        try:
            from ..cache.cache_manager import get_cache
            
            cache = get_cache()
            if cache:
                # Ping 테스트
                test_key = "_health_check_"
                await cache.set(test_key, "test", ttl=10)
                value = await cache.get(test_key)
                
                if value == "test":
                    stats = await cache.get_stats()
                    return ComponentHealth(
                        name="redis",
                        status=HealthStatus.HEALTHY,
                        message="Redis connection successful",
                        details=stats
                    )
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Redis not available (using memory cache)"
            )
            
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check failed: {e}"
            )
    
    async def _check_kafka(self) -> ComponentHealth:
        """Kafka 체크"""
        try:
            from ..messaging.kafka_client import get_message_queue
            
            mq = get_message_queue()
            if mq:
                stats = mq.get_stats()
                return ComponentHealth(
                    name="kafka",
                    status=HealthStatus.HEALTHY,
                    message="Kafka connection successful",
                    details=stats
                )
            
            return ComponentHealth(
                name="kafka",
                status=HealthStatus.DEGRADED,
                message="Kafka not available"
            )
            
        except Exception as e:
            return ComponentHealth(
                name="kafka",
                status=HealthStatus.UNHEALTHY,
                message=f"Kafka check failed: {e}"
            )
    
    async def _check_api(self) -> ComponentHealth:
        """API 체크"""
        try:
            # API 엔드포인트 체크
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return ComponentHealth(
                            name="api",
                            status=HealthStatus.HEALTHY,
                            message="API is responsive"
                        )
                    else:
                        return ComponentHealth(
                            name="api",
                            status=HealthStatus.DEGRADED,
                            message=f"API returned status {response.status}"
                        )
                        
        except asyncio.TimeoutError:
            return ComponentHealth(
                name="api",
                status=HealthStatus.UNHEALTHY,
                message="API request timeout"
            )
        except Exception as e:
            return ComponentHealth(
                name="api",
                status=HealthStatus.UNHEALTHY,
                message=f"API check failed: {e}"
            )
    
    async def _check_disk_space(self) -> ComponentHealth:
        """디스크 공간 체크"""
        try:
            import shutil
            
            usage = shutil.disk_usage("/")
            percent_used = (usage.used / usage.total) * 100
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk space critical: {percent_used:.1f}% used"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk space warning: {percent_used:.1f}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space OK: {percent_used:.1f}% used"
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent_used": percent_used
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {e}"
            )
    
    async def _check_memory(self) -> ComponentHealth:
        """메모리 체크"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical: {percent_used:.1f}%"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = f"Memory usage warning: {percent_used:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage OK: {percent_used:.1f}%"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "percent_used": percent_used
                }
            )
            
        except ImportError:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.DEGRADED,
                message="psutil not available"
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {e}"
            )
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self.check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
            self.check_task = None
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)


# 글로벌 헬스 체커
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> Optional[HealthChecker]:
    """헬스 체커 반환"""
    global _health_checker
    
    if _health_checker is None:
        _health_checker = HealthChecker()
    
    return _health_checker
