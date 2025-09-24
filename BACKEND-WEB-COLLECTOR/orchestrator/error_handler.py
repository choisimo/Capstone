"""
에러 처리 및 재시도 시스템
강건한 에러 복구와 재시도 전략
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import traceback
import functools

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """에러 심각도"""
    CRITICAL = "critical"  # 시스템 중단 필요
    HIGH = "high"  # 즉시 조치 필요
    MEDIUM = "medium"  # 조치 필요
    LOW = "low"  # 모니터링
    INFO = "info"  # 정보성


class RetryStrategy(Enum):
    """재시도 전략"""
    EXPONENTIAL = "exponential"  # 지수 백오프
    LINEAR = "linear"  # 선형 증가
    FIXED = "fixed"  # 고정 간격
    FIBONACCI = "fibonacci"  # 피보나치
    CUSTOM = "custom"  # 사용자 정의


@dataclass
class RetryPolicy:
    """재시도 정책"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    initial_delay: float = 1.0  # 초
    max_delay: float = 300.0  # 최대 5분
    multiplier: float = 2.0
    jitter: bool = True  # 무작위 지연 추가
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    non_retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """재시도 여부 결정"""
        if attempt >= self.max_attempts:
            return False
        
        # 재시도 불가능한 예외
        if self.non_retryable_exceptions:
            for exc_type in self.non_retryable_exceptions:
                if isinstance(exception, exc_type):
                    return False
        
        # 재시도 가능한 예외
        if self.retryable_exceptions:
            for exc_type in self.retryable_exceptions:
                if isinstance(exception, exc_type):
                    return True
            return False  # 목록에 없으면 재시도 안 함
        
        return True  # 기본적으로 재시도
    
    def get_delay(self, attempt: int) -> float:
        """재시도 지연 시간 계산"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.multiplier ** (attempt - 1))
        
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        
        elif self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci_delay(attempt)
        
        else:
            delay = self.initial_delay
        
        # 최대 지연 제한
        delay = min(delay, self.max_delay)
        
        # Jitter 추가
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def _fibonacci_delay(self, n: int) -> float:
        """피보나치 지연 계산"""
        if n <= 0:
            return self.initial_delay
        elif n == 1:
            return self.initial_delay
        else:
            a, b = self.initial_delay, self.initial_delay
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b


@dataclass
class ErrorContext:
    """에러 컨텍스트"""
    error_id: str
    exception: Exception
    error_type: str
    error_message: str
    traceback: str
    timestamp: datetime
    component: str
    operation: str
    severity: ErrorSeverity
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "severity": self.severity.value,
            "retry_count": self.retry_count,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "metadata": self.metadata
        }


class CircuitBreaker:
    """서킷 브레이커 패턴"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """함수 호출"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """비동기 함수 호출"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """성공 처리"""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """실패 처리"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def _should_attempt_reset(self) -> bool:
        """리셋 시도 여부"""
        if self.last_failure_time:
            elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
            return elapsed >= self.recovery_timeout
        return False


class ErrorHandler:
    """
    에러 처리기
    
    중앙 집중식 에러 처리 및 복구
    """
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self.default_retry_policy = RetryPolicy()
        self.error_callbacks: List[Callable] = []
        self.statistics = {
            "total_errors": 0,
            "resolved_errors": 0,
            "retried_operations": 0,
            "circuit_breaks": 0
        }
        self.logger = logger
    
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ):
        """에러 핸들러 등록"""
        self.error_handlers[exception_type] = handler
        self.logger.info(f"Registered handler for {exception_type.__name__}")
    
    def register_retry_policy(
        self,
        operation: str,
        policy: RetryPolicy
    ):
        """재시도 정책 등록"""
        self.retry_policies[operation] = policy
        self.logger.info(f"Registered retry policy for {operation}")
    
    def register_circuit_breaker(
        self,
        service: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        """서킷 브레이커 등록"""
        self.circuit_breakers[service] = CircuitBreaker(
            failure_threshold,
            recovery_timeout
        )
        self.logger.info(f"Registered circuit breaker for {service}")
    
    async def handle_error(
        self,
        exception: Exception,
        component: str,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        에러 처리
        
        Args:
            exception: 발생한 예외
            component: 컴포넌트 이름
            operation: 작업 이름
            severity: 심각도
            metadata: 추가 메타데이터
        
        Returns:
            에러 컨텍스트
        """
        import uuid
        
        # 에러 컨텍스트 생성
        error_context = ErrorContext(
            error_id=str(uuid.uuid4()),
            exception=exception,
            error_type=type(exception).__name__,
            error_message=str(exception),
            traceback=traceback.format_exc(),
            timestamp=datetime.utcnow(),
            component=component,
            operation=operation,
            severity=severity,
            metadata=metadata or {}
        )
        
        # 히스토리 저장
        self.error_history.append(error_context)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        self.statistics["total_errors"] += 1
        
        # 로깅
        self._log_error(error_context)
        
        # 핸들러 실행
        handled = await self._run_handler(error_context)
        
        if handled:
            error_context.resolved = True
            self.statistics["resolved_errors"] += 1
        
        # 콜백 실행
        await self._run_callbacks(error_context)
        
        # 심각한 에러 처리
        if severity == ErrorSeverity.CRITICAL:
            await self._handle_critical_error(error_context)
        
        return error_context
    
    async def _run_handler(self, error_context: ErrorContext) -> bool:
        """에러 핸들러 실행"""
        exception = error_context.exception
        
        for exc_type, handler in self.error_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        resolution = await handler(error_context)
                    else:
                        resolution = await asyncio.to_thread(handler, error_context)
                    
                    if resolution:
                        error_context.resolution = str(resolution)
                        return True
                        
                except Exception as e:
                    self.logger.error(f"Error handler failed: {e}")
        
        return False
    
    async def _run_callbacks(self, error_context: ErrorContext):
        """콜백 실행"""
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error_context)
                else:
                    await asyncio.to_thread(callback, error_context)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")
    
    async def _handle_critical_error(self, error_context: ErrorContext):
        """치명적 에러 처리"""
        self.logger.critical(
            f"CRITICAL ERROR in {error_context.component}: {error_context.error_message}"
        )
        
        # 알림 발송, 시스템 종료 등의 처리
        # 실제 구현은 시스템 요구사항에 따라
    
    def _log_error(self, error_context: ErrorContext):
        """에러 로깅"""
        log_message = (
            f"Error in {error_context.component}.{error_context.operation}: "
            f"{error_context.error_message}"
        )
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    async def retry_with_policy(
        self,
        func: Callable,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """
        재시도 정책으로 함수 실행
        
        Args:
            func: 실행할 함수
            operation: 작업 이름
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
        
        Returns:
            함수 실행 결과
        """
        policy = self.retry_policies.get(operation, self.default_retry_policy)
        last_exception = None
        
        for attempt in range(1, policy.max_attempts + 1):
            try:
                # 서킷 브레이커 확인
                if operation in self.circuit_breakers:
                    breaker = self.circuit_breakers[operation]
                    if asyncio.iscoroutinefunction(func):
                        return await breaker.async_call(func, *args, **kwargs)
                    else:
                        return breaker.call(func, *args, **kwargs)
                
                # 일반 실행
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await asyncio.to_thread(func, *args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if not policy.should_retry(e, attempt):
                    raise
                
                if attempt < policy.max_attempts:
                    delay = policy.get_delay(attempt)
                    self.logger.info(
                        f"Retrying {operation} (attempt {attempt}/{policy.max_attempts}) "
                        f"after {delay:.1f}s"
                    )
                    self.statistics["retried_operations"] += 1
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    def add_error_callback(self, callback: Callable):
        """에러 콜백 추가"""
        self.error_callbacks.append(callback)
    
    def get_recent_errors(
        self,
        limit: int = 100,
        severity: Optional[ErrorSeverity] = None,
        component: Optional[str] = None
    ) -> List[ErrorContext]:
        """최근 에러 조회"""
        filtered = self.error_history
        
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        
        if component:
            filtered = [e for e in filtered if e.component == component]
        
        return filtered[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        severity_counts = {}
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            **self.statistics,
            "error_history_size": len(self.error_history),
            "severity_distribution": severity_counts,
            "circuit_breakers": len(self.circuit_breakers),
            "retry_policies": len(self.retry_policies)
        }


def with_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    initial_delay: float = 1.0,
    retryable_exceptions: List[Type[Exception]] = None
):
    """
    재시도 데코레이터
    
    Args:
        max_attempts: 최대 시도 횟수
        strategy: 재시도 전략
        initial_delay: 초기 지연
        retryable_exceptions: 재시도 가능한 예외
    """
    def decorator(func):
        policy = RetryPolicy(
            max_attempts=max_attempts,
            strategy=strategy,
            initial_delay=initial_delay,
            retryable_exceptions=retryable_exceptions or []
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not policy.should_retry(e, attempt):
                        raise
                    
                    if attempt < policy.max_attempts:
                        delay = policy.get_delay(attempt)
                        await asyncio.sleep(delay)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not policy.should_retry(e, attempt):
                        raise
                    
                    if attempt < policy.max_attempts:
                        delay = policy.get_delay(attempt)
                        import time
                        time.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
