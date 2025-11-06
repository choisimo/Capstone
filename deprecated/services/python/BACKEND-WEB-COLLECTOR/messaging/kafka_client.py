"""
Kafka 클라이언트
프로듀서 및 컨슈머 구현
"""
import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    from kafka.errors import KafkaConnectionError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from .message_models import Message, MessageType

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka 프로듀서"""
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        value_serializer: Optional[Callable] = None,
        key_serializer: Optional[Callable] = None,
        compression_type: str = "gzip",
        acks: str = "all",
        max_batch_size: int = 16384,
        linger_ms: int = 100
    ):
        """
        초기화
        
        Args:
            bootstrap_servers: Kafka 서버 주소
            value_serializer: 값 직렬화 함수
            key_serializer: 키 직렬화 함수
            compression_type: 압축 타입
            acks: 확인 수준
            max_batch_size: 최대 배치 크기
            linger_ms: 배치 대기 시간
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("aiokafka package not installed")
        
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        
        self.value_serializer = value_serializer or self._default_serializer
        self.key_serializer = key_serializer or self._default_key_serializer
        
        self.producer_config = {
            "bootstrap_servers": self.bootstrap_servers.split(","),
            "value_serializer": self.value_serializer,
            "key_serializer": self.key_serializer,
            "compression_type": compression_type,
            "acks": acks,
            "max_batch_size": max_batch_size,
            "linger_ms": linger_ms
        }
        
        self.producer: Optional[AIOKafkaProducer] = None
        self.stats = {
            "sent": 0,
            "failed": 0,
            "errors": 0
        }
    
    def _default_serializer(self, value: Any) -> bytes:
        """기본 직렬화"""
        if isinstance(value, Message):
            return value.json().encode("utf-8")
        elif isinstance(value, dict):
            return json.dumps(value).encode("utf-8")
        elif isinstance(value, str):
            return value.encode("utf-8")
        else:
            return json.dumps(value).encode("utf-8")
    
    def _default_key_serializer(self, key: Any) -> Optional[bytes]:
        """키 직렬화"""
        if key is None:
            return None
        return str(key).encode("utf-8")
    
    async def start(self):
        """프로듀서 시작"""
        try:
            self.producer = AIOKafkaProducer(**self.producer_config)
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self):
        """프로듀서 종료"""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")
    
    async def send(
        self,
        topic: str,
        value: Any,
        key: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        메시지 발송
        
        Args:
            topic: 토픽명
            value: 메시지 값
            key: 메시지 키
            headers: 헤더
        
        Returns:
            성공 여부
        """
        if not self.producer:
            logger.error("Producer not started")
            return False
        
        try:
            # 헤더 변환
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode("utf-8") if isinstance(v, str) else v)
                    for k, v in headers.items()
                ]
            
            # 메시지 전송
            await self.producer.send(
                topic,
                value=value,
                key=key,
                headers=kafka_headers
            )
            
            self.stats["sent"] += 1
            logger.debug(f"Message sent to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            self.stats["failed"] += 1
            return False
    
    async def send_batch(
        self,
        topic: str,
        messages: List[Any]
    ) -> int:
        """
        배치 전송
        
        Args:
            topic: 토픽명
            messages: 메시지 리스트
        
        Returns:
            성공한 메시지 수
        """
        if not self.producer:
            logger.error("Producer not started")
            return 0
        
        success_count = 0
        for message in messages:
            if await self.send(topic, message):
                success_count += 1
        
        # 플러시
        await self.producer.flush()
        
        return success_count
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            **self.stats,
            "success_rate": self.stats["sent"] / 
                          (self.stats["sent"] + self.stats["failed"])
                          if (self.stats["sent"] + self.stats["failed"]) > 0 else 0
        }


class KafkaConsumer:
    """Kafka 컨슈머"""
    
    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None,
        value_deserializer: Optional[Callable] = None,
        key_deserializer: Optional[Callable] = None,
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
        max_poll_records: int = 100,
        session_timeout_ms: int = 30000
    ):
        """
        초기화
        
        Args:
            topics: 구독할 토픽 리스트
            group_id: 컨슈머 그룹 ID
            bootstrap_servers: Kafka 서버
            value_deserializer: 값 역직렬화
            key_deserializer: 키 역직렬화
            auto_offset_reset: 오프셋 리셋 정책
            enable_auto_commit: 자동 커밋 여부
            max_poll_records: 최대 폴링 레코드
            session_timeout_ms: 세션 타임아웃
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("aiokafka package not installed")
        
        self.topics = topics
        self.group_id = group_id
        
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        
        self.value_deserializer = value_deserializer or self._default_deserializer
        self.key_deserializer = key_deserializer or self._default_key_deserializer
        
        self.consumer_config = {
            "bootstrap_servers": self.bootstrap_servers.split(","),
            "group_id": group_id,
            "value_deserializer": self.value_deserializer,
            "key_deserializer": self.key_deserializer,
            "auto_offset_reset": auto_offset_reset,
            "enable_auto_commit": enable_auto_commit,
            "max_poll_records": max_poll_records,
            "session_timeout_ms": session_timeout_ms
        }
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.handlers: Dict[str, List[Callable]] = {}
        
        self.stats = {
            "received": 0,
            "processed": 0,
            "errors": 0
        }
    
    def _default_deserializer(self, value: bytes) -> Any:
        """기본 역직렬화"""
        try:
            return json.loads(value.decode("utf-8"))
        except:
            return value.decode("utf-8")
    
    def _default_key_deserializer(self, key: Optional[bytes]) -> Optional[str]:
        """키 역직렬화"""
        if key is None:
            return None
        return key.decode("utf-8")
    
    async def start(self):
        """컨슈머 시작"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                **self.consumer_config
            )
            await self.consumer.start()
            self.running = True
            logger.info(f"Kafka consumer started: {self.topics}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def stop(self):
        """컨슈머 종료"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            logger.info("Kafka consumer stopped")
    
    def register_handler(
        self,
        topic: str,
        handler: Callable
    ):
        """
        핸들러 등록
        
        Args:
            topic: 토픽명
            handler: 메시지 핸들러
        """
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
    
    async def consume(
        self,
        max_messages: Optional[int] = None
    ):
        """
        메시지 소비
        
        Args:
            max_messages: 최대 메시지 수
        """
        if not self.consumer:
            logger.error("Consumer not started")
            return
        
        message_count = 0
        
        async for message in self.consumer:
            if not self.running:
                break
            
            self.stats["received"] += 1
            
            # 메시지 처리
            try:
                await self._process_message(message)
                self.stats["processed"] += 1
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self.stats["errors"] += 1
            
            message_count += 1
            if max_messages and message_count >= max_messages:
                break
    
    async def _process_message(self, message):
        """메시지 처리"""
        topic = message.topic
        value = message.value
        
        # 핸들러 실행
        if topic in self.handlers:
            for handler in self.handlers[topic]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(value)
                    else:
                        handler(value)
                except Exception as e:
                    logger.error(f"Handler error for topic {topic}: {e}")
                    raise
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            **self.stats,
            "processing_rate": self.stats["processed"] / self.stats["received"]
                              if self.stats["received"] > 0 else 0
        }


class MessageQueue:
    """메시지 큐 매니저"""
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        producer_config: Optional[Dict] = None,
        consumer_config: Optional[Dict] = None
    ):
        """
        초기화
        
        Args:
            bootstrap_servers: Kafka 서버
            producer_config: 프로듀서 설정
            consumer_config: 컨슈머 설정
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        
        # 프로듀서
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **(producer_config or {})
        )
        
        # 컨슈머 풀
        self.consumers: Dict[str, KafkaConsumer] = {}
        self.consumer_config = consumer_config or {}
        
        # 토픽 매핑
        self.topics = {
            MessageType.TASK_CREATED: "hybrid-crawler.tasks",
            MessageType.TASK_COMPLETED: "hybrid-crawler.tasks",
            MessageType.TASK_FAILED: "hybrid-crawler.tasks",
            
            MessageType.SCRAPE_REQUESTED: "hybrid-crawler.scraping",
            MessageType.SCRAPE_COMPLETED: "hybrid-crawler.scraping",
            
            MessageType.ANALYSIS_REQUESTED: "hybrid-crawler.analysis",
            MessageType.ANALYSIS_COMPLETED: "hybrid-crawler.analysis",
            
            MessageType.CHANGE_DETECTED: "hybrid-crawler.monitoring",
            MessageType.MONITOR_STARTED: "hybrid-crawler.monitoring",
            
            MessageType.SYSTEM_ERROR: "hybrid-crawler.system",
            MessageType.SYSTEM_WARNING: "hybrid-crawler.system",
        }
    
    async def start(self):
        """메시지 큐 시작"""
        await self.producer.start()
        logger.info("Message queue started")
    
    async def stop(self):
        """메시지 큐 종료"""
        # 모든 컨슈머 종료
        for consumer in self.consumers.values():
            await consumer.stop()
        
        # 프로듀서 종료
        await self.producer.stop()
        
        logger.info("Message queue stopped")
    
    async def publish(
        self,
        message: Message,
        topic: Optional[str] = None
    ) -> bool:
        """
        메시지 발행
        
        Args:
            message: 메시지
            topic: 토픽 (기본값: 메시지 타입에 따라 결정)
        
        Returns:
            성공 여부
        """
        # 토픽 결정
        if topic is None:
            topic = self.topics.get(
                message.type,
                "hybrid-crawler.default"
            )
        
        # 헤더 생성
        headers = {
            "message_id": message.id,
            "message_type": message.type,
            "source": message.source,
            "timestamp": message.timestamp.isoformat()
        }
        
        if message.correlation_id:
            headers["correlation_id"] = message.correlation_id
        
        # 메시지 전송
        return await self.producer.send(
            topic=topic,
            value=message,
            key=message.id,
            headers=headers
        )
    
    async def subscribe(
        self,
        topics: List[str],
        group_id: str,
        handler: Callable,
        **consumer_kwargs
    ) -> KafkaConsumer:
        """
        토픽 구독
        
        Args:
            topics: 토픽 리스트
            group_id: 컨슈머 그룹 ID
            handler: 메시지 핸들러
            **consumer_kwargs: 추가 컨슈머 설정
        
        Returns:
            컨슈머 인스턴스
        """
        # 컨슈머 생성
        consumer = KafkaConsumer(
            topics=topics,
            group_id=group_id,
            bootstrap_servers=self.bootstrap_servers,
            **{**self.consumer_config, **consumer_kwargs}
        )
        
        # 핸들러 등록
        for topic in topics:
            consumer.register_handler(topic, handler)
        
        # 시작
        await consumer.start()
        
        # 저장
        consumer_id = f"{group_id}:{','.join(topics)}"
        self.consumers[consumer_id] = consumer
        
        # 비동기 소비 시작
        asyncio.create_task(consumer.consume())
        
        return consumer
    
    async def unsubscribe(self, consumer_id: str):
        """구독 해제"""
        if consumer_id in self.consumers:
            await self.consumers[consumer_id].stop()
            del self.consumers[consumer_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            "producer": self.producer.get_stats(),
            "consumers": {
                cid: consumer.get_stats()
                for cid, consumer in self.consumers.items()
            }
        }


# 글로벌 메시지 큐
_message_queue: Optional[MessageQueue] = None


def init_message_queue(
    bootstrap_servers: Optional[str] = None,
    **kwargs
) -> Optional[MessageQueue]:
    """
    메시지 큐 초기화
    
    Args:
        bootstrap_servers: Kafka 서버
        **kwargs: 추가 설정
    
    Returns:
        MessageQueue 인스턴스
    """
    global _message_queue
    
    if not KAFKA_AVAILABLE:
        logger.warning("Kafka not available, message queue disabled")
        return None
    
    if _message_queue is None:
        try:
            _message_queue = MessageQueue(
                bootstrap_servers=bootstrap_servers,
                **kwargs
            )
            logger.info("Message queue initialized")
        except Exception as e:
            logger.error(f"Failed to initialize message queue: {e}")
            _message_queue = None
    
    return _message_queue


def get_message_queue() -> Optional[MessageQueue]:
    """메시지 큐 인스턴스 반환"""
    return _message_queue


async def close_message_queue():
    """메시지 큐 종료"""
    global _message_queue
    
    if _message_queue:
        await _message_queue.stop()
        _message_queue = None
        logger.info("Message queue closed")
