"""
공통 HTTP 클라이언트 유틸리티
타임아웃, 재시도, 회로 차단기 표준화
작성일: 2025-09-26
"""

import time
import hashlib
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """회로 차단기 상태"""
    CLOSED = "closed"  # 정상 작동
    OPEN = "open"      # 차단 (실패)
    HALF_OPEN = "half_open"  # 복구 시도


@dataclass
class CircuitBreakerConfig:
    """회로 차단기 설정"""
    failure_threshold: int = 5  # 실패 임계값
    recovery_timeout: int = 60  # 복구 대기 시간 (초)
    expected_exception: type = Exception  # 예상 예외 타입


@dataclass
class HTTPClientConfig:
    """HTTP 클라이언트 설정"""
    # 타임아웃 설정
    connect_timeout: float = 2.0  # 연결 타임아웃
    read_timeout: float = 5.0      # 읽기 타임아웃 (외부)
    internal_read_timeout: float = 2.0  # 내부 서비스 읽기 타임아웃
    
    # 재시도 설정
    max_retries: int = 3          # 최대 재시도 횟수
    retry_budget: float = 2.0      # 재시도 예산 (초)
    
    # 회로 차단기 설정
    circuit_breaker: Optional[CircuitBreakerConfig] = field(default_factory=CircuitBreakerConfig)
    
    # 헤더 설정
    default_headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "PensionSentimentService/1.0"
    })


class CircuitBreaker:
    """회로 차단기 구현"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
    def call(self, func: Callable, *args, **kwargs):
        """회로 차단기를 통한 함수 호출"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """복구 시도 여부 확인"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self):
        """성공 시 처리"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count > 2:  # 3번 연속 성공 시 회로 닫기
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker CLOSED")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """실패 시 처리"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


class ReliableHTTPClient:
    """신뢰할 수 있는 HTTP 클라이언트"""
    
    def __init__(self, config: Optional[HTTPClientConfig] = None, is_internal: bool = False):
        """
        Args:
            config: HTTP 클라이언트 설정
            is_internal: 내부 서비스 호출 여부
        """
        self.config = config or HTTPClientConfig()
        self.is_internal = is_internal
        
        # 타임아웃 설정
        read_timeout = self.config.internal_read_timeout if is_internal else self.config.read_timeout
        self.timeout = httpx.Timeout(
            connect=self.config.connect_timeout,
            read=read_timeout,
            write=5.0,
            pool=5.0
        )
        
        # HTTP 클라이언트 생성
        self.client = httpx.Client(
            timeout=self.timeout,
            headers=self.config.default_headers,
            follow_redirects=True
        )
        
        # 회로 차단기 생성
        self.circuit_breaker = CircuitBreaker(self.config.circuit_breaker) if self.config.circuit_breaker else None
    
    def get_deterministic_jitter(self, attempt: int, url: str) -> float:
        """결정론적 지터 계산 (해시 기반)"""
        # URL과 시도 횟수를 기반으로 해시 생성
        hash_input = f"{url}:{attempt}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        
        # 0.1 ~ 0.5초 사이의 지터 생성
        jitter = 0.1 + (hash_value % 400) / 1000
        return jitter
    
    @retry(
        stop=(stop_after_attempt(3) | stop_after_delay(2)),  # 3회 또는 2초
        wait=wait_fixed(0.5),  # 기본 대기 시간
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=before_sleep_log(logger, logging.DEBUG)
    )
    def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """HTTP 요청 실행 (재시도 포함)"""
        # 결정론적 지터 추가
        attempt = getattr(self._make_request.retry, 'statistics', {}).get('attempt_number', 1)
        jitter = self.get_deterministic_jitter(attempt, url)
        time.sleep(jitter)
        
        # 요청 실행
        response = self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """HTTP 요청 (회로 차단기 포함)"""
        if self.circuit_breaker:
            return self.circuit_breaker.call(self._make_request, method, url, **kwargs)
        return self._make_request(method, url, **kwargs)
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """GET 요청"""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        """POST 요청"""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT 요청"""
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE 요청"""
        return self.request("DELETE", url, **kwargs)
    
    def close(self):
        """클라이언트 종료"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# 사전 설정된 클라이언트 생성 함수
def create_external_client(config: Optional[HTTPClientConfig] = None) -> ReliableHTTPClient:
    """외부 서비스용 클라이언트 생성"""
    return ReliableHTTPClient(config, is_internal=False)


def create_internal_client(config: Optional[HTTPClientConfig] = None) -> ReliableHTTPClient:
    """내부 서비스용 클라이언트 생성"""
    return ReliableHTTPClient(config, is_internal=True)


# 유효성 검증 함수
def validate_url(url: str) -> bool:
    """URL 유효성 검증 (http/https만 허용)"""
    if not url:
        return False
    
    # javascript: 등 비정상 스킴 차단
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL scheme: {url}")
        return False
    
    # 금지된 패턴 검사
    forbidden_patterns = ['javascript:', 'data:', 'vbscript:', 'about:']
    for pattern in forbidden_patterns:
        if pattern in url.lower():
            logger.error(f"Forbidden pattern in URL: {pattern}")
            return False
    
    return True
