"""
이벤트 버스 시스템
비동기 이벤트 기반 통신
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """이벤트 타입"""
    # 작업 관련
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # 스크래핑 관련
    SCRAPE_STARTED = "scrape_started"
    SCRAPE_COMPLETED = "scrape_completed"
    SCRAPE_FAILED = "scrape_failed"
    
    # 모니터링 관련
    MONITOR_STARTED = "monitor_started"
    MONITOR_STOPPED = "monitor_stopped"
    CHANGE_DETECTED = "change_detected"
    
    # 분석 관련
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    
    # 시스템 관련
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"


@dataclass
class Event:
    """이벤트 데이터"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_INFO
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """JSON 변환"""
        return json.dumps(self.to_dict(), default=str)


class EventHandler:
    """이벤트 핸들러 베이스 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.filter_types: Set[EventType] = set()
        self.filter_sources: Set[str] = set()
    
    async def handle(self, event: Event) -> Any:
        """이벤트 처리"""
        raise NotImplementedError
    
    def should_handle(self, event: Event) -> bool:
        """이벤트 처리 여부 결정"""
        # 타입 필터
        if self.filter_types and event.event_type not in self.filter_types:
            return False
        
        # 소스 필터
        if self.filter_sources and event.source not in self.filter_sources:
            return False
        
        return True


class CallbackEventHandler(EventHandler):
    """콜백 기반 이벤트 핸들러"""
    
    def __init__(self, name: str, callback: Callable):
        super().__init__(name)
        self.callback = callback
    
    async def handle(self, event: Event) -> Any:
        """이벤트 처리"""
        if asyncio.iscoroutinefunction(self.callback):
            return await self.callback(event)
        else:
            return await asyncio.to_thread(self.callback, event)


class EventBus:
    """
    이벤트 버스
    
    비동기 이벤트 발행/구독 시스템
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self.handlers: Dict[str, EventHandler] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.event_history: List[Event] = []
        self.max_history_size = 10000
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self.statistics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0
        }
        self.logger = logger
    
    async def start(self):
        """이벤트 버스 시작"""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        self.logger.info("Event bus started")
    
    async def stop(self):
        """이벤트 버스 중지"""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Event bus stopped")
    
    async def _process_events(self):
        """이벤트 처리 루프"""
        while self._running:
            try:
                # 이벤트 대기
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                if event:
                    await self._handle_event(event)
                    self.statistics["events_processed"] += 1
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")
                self.statistics["events_failed"] += 1
    
    async def _handle_event(self, event: Event):
        """이벤트 처리"""
        self.logger.debug(f"Processing event: {event.event_type.value} from {event.source}")
        
        # 히스토리 저장
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # 핸들러 실행
        tasks = []
        for handler in self.handlers.values():
            if handler.should_handle(event):
                task = asyncio.create_task(self._execute_handler(handler, event))
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 에러 로깅
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Handler error: {result}")
    
    async def _execute_handler(self, handler: EventHandler, event: Event):
        """핸들러 실행"""
        try:
            return await handler.handle(event)
        except Exception as e:
            self.logger.error(f"Handler {handler.name} failed: {e}")
            raise
    
    async def publish(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        이벤트 발행
        
        Args:
            event_type: 이벤트 타입
            source: 이벤트 소스
            data: 이벤트 데이터
            metadata: 메타데이터
        
        Returns:
            이벤트 ID
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            metadata=metadata or {}
        )
        
        try:
            await self.event_queue.put(event)
            self.statistics["events_published"] += 1
            self.logger.debug(f"Published event: {event.event_type.value}")
            return event.event_id
            
        except asyncio.QueueFull:
            self.logger.error("Event queue full")
            raise
    
    def subscribe(
        self,
        handler: EventHandler
    ) -> str:
        """
        이벤트 구독
        
        Args:
            handler: 이벤트 핸들러
        
        Returns:
            핸들러 ID
        """
        handler_id = str(uuid.uuid4())
        self.handlers[handler_id] = handler
        self.logger.info(f"Subscribed handler: {handler.name}")
        return handler_id
    
    def subscribe_callback(
        self,
        callback: Callable,
        event_types: List[EventType] = None,
        sources: List[str] = None,
        name: str = None
    ) -> str:
        """
        콜백 함수 구독
        
        Args:
            callback: 콜백 함수
            event_types: 구독할 이벤트 타입
            sources: 구독할 소스
            name: 핸들러 이름
        
        Returns:
            핸들러 ID
        """
        handler_name = name or f"callback_{uuid.uuid4().hex[:8]}"
        handler = CallbackEventHandler(handler_name, callback)
        
        if event_types:
            handler.filter_types = set(event_types)
        
        if sources:
            handler.filter_sources = set(sources)
        
        return self.subscribe(handler)
    
    def unsubscribe(self, handler_id: str) -> bool:
        """구독 해제"""
        if handler_id in self.handlers:
            handler = self.handlers[handler_id]
            del self.handlers[handler_id]
            self.logger.info(f"Unsubscribed handler: {handler.name}")
            return True
        return False
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        이벤트 히스토리 조회
        
        Args:
            event_type: 필터링할 이벤트 타입
            source: 필터링할 소스
            limit: 최대 개수
        
        Returns:
            이벤트 리스트
        """
        filtered = self.event_history
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        if source:
            filtered = [e for e in filtered if e.source == source]
        
        return filtered[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            **self.statistics,
            "handlers_count": len(self.handlers),
            "queue_size": self.event_queue.qsize(),
            "history_size": len(self.event_history)
        }
    
    def clear_history(self):
        """히스토리 초기화"""
        self.event_history.clear()
        self.logger.info("Event history cleared")
