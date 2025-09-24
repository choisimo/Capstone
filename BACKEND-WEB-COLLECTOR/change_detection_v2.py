"""
ChangeDetection 서비스 v2.0
개선된 웹 변경 감지 시스템
"""
import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import difflib
from urllib.parse import urlparse
import aiohttp

from gemini_client_v2 import GeminiClientV2
from prompts.change import IntelligentChangeAnalysisPromptTemplate
from parsers.structured_parser import StructuredDataParser

logger = logging.getLogger(__name__)


class MonitoringStrategy(Enum):
    """모니터링 전략"""
    FULL_CONTENT = "full_content"  # 전체 콘텐츠
    SMART_DIFF = "smart_diff"  # 스마트 차이점
    STRUCTURE_ONLY = "structure_only"  # 구조만
    AI_ANALYSIS = "ai_analysis"  # AI 분석
    KEYWORD_BASED = "keyword_based"  # 키워드 기반


class ChangeType(Enum):
    """변경 유형"""
    CONTENT_UPDATE = "content_update"
    STRUCTURE_CHANGE = "structure_change"
    NEW_CONTENT = "new_content"
    REMOVED_CONTENT = "removed_content"
    METADATA_CHANGE = "metadata_change"
    NO_CHANGE = "no_change"


class NotificationPriority(Enum):
    """알림 우선순위"""
    CRITICAL = "critical"  # 즉시 알림
    HIGH = "high"  # 높은 우선순위
    MEDIUM = "medium"  # 중간
    LOW = "low"  # 낮음
    INFO = "info"  # 정보성


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    url: str
    strategy: MonitoringStrategy = MonitoringStrategy.SMART_DIFF
    check_interval: timedelta = timedelta(hours=1)
    keywords: List[str] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)
    notification_threshold: float = 0.3
    ai_analysis: bool = True
    store_history: bool = True
    max_history_size: int = 100
    custom_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeEvent:
    """변경 이벤트"""
    event_id: str
    url: str
    timestamp: datetime
    change_type: ChangeType
    change_summary: str
    importance_score: float
    notification_priority: NotificationPriority
    before_content: Optional[str] = None
    after_content: Optional[str] = None
    diff_details: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "event_id": self.event_id,
            "url": self.url,
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type.value,
            "change_summary": self.change_summary,
            "importance_score": self.importance_score,
            "notification_priority": self.notification_priority.value,
            "diff_details": self.diff_details,
            "ai_analysis": self.ai_analysis,
            "metadata": self.metadata
        }


class EventBus:
    """이벤트 버스"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[ChangeEvent] = []
        self.max_history = 1000
    
    async def publish(self, event: ChangeEvent):
        """이벤트 발행"""
        # 히스토리 저장
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # 구독자에게 전달
        event_type = event.change_type.value
        
        # 특정 타입 구독자
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Event callback failed: {e}")
        
        # 전체 구독자
        if '*' in self.subscribers:
            for callback in self.subscribers['*']:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Event callback failed: {e}")
    
    def subscribe(self, event_type: str, callback: Callable):
        """이벤트 구독"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """구독 해제"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)


class ContentStore:
    """콘텐츠 저장소"""
    
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.history: Dict[str, List[Dict[str, Any]]] = {}
    
    def save(self, url: str, content: str, metadata: Optional[Dict] = None):
        """콘텐츠 저장"""
        content_hash = self._hash_content(content)
        timestamp = datetime.utcnow()
        
        entry = {
            "content": content,
            "hash": content_hash,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        # 현재 콘텐츠
        self.store[url] = entry
        
        # 히스토리
        if url not in self.history:
            self.history[url] = []
        self.history[url].append(entry)
        
        # 히스토리 크기 제한
        if len(self.history[url]) > 100:
            self.history[url] = self.history[url][-100:]
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """콘텐츠 조회"""
        return self.store.get(url)
    
    def get_history(self, url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """히스토리 조회"""
        history = self.history.get(url, [])
        return history[-limit:]
    
    def _hash_content(self, content: str) -> str:
        """콘텐츠 해시"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def has_changed(self, url: str, new_content: str) -> bool:
        """변경 여부 확인"""
        current = self.get(url)
        if not current:
            return True
        
        new_hash = self._hash_content(new_content)
        return new_hash != current['hash']


class ChangeDetectionServiceV2:
    """
    개선된 ChangeDetection 서비스
    
    특징:
    - 모듈화된 구조
    - 이벤트 기반 아키텍처
    - AI 변경 분석
    - 유연한 모니터링 전략
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        enable_ai: bool = True
    ):
        self.gemini_client = GeminiClientV2(api_key=gemini_api_key) if enable_ai else None
        self.change_prompt = IntelligentChangeAnalysisPromptTemplate()
        self.parser = StructuredDataParser()
        
        # 컴포넌트
        self.event_bus = EventBus()
        self.content_store = ContentStore()
        
        # 모니터링 목록
        self.monitoring_configs: Dict[str, MonitoringConfig] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # 세션
        self._session: Optional[aiohttp.ClientSession] = None
        
        self.logger = logger
    
    async def __aenter__(self):
        """비동기 컨텍스트 진입"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 종료"""
        await self.stop_all_monitoring()
        if self._session:
            await self._session.close()
    
    async def add_monitoring(
        self,
        config: MonitoringConfig,
        start_immediately: bool = True
    ) -> str:
        """
        모니터링 추가
        
        Args:
            config: 모니터링 설정
            start_immediately: 즉시 시작 여부
        
        Returns:
            모니터링 ID
        """
        monitoring_id = self._generate_monitoring_id(config.url)
        self.monitoring_configs[monitoring_id] = config
        
        if start_immediately:
            await self.start_monitoring(monitoring_id)
        
        self.logger.info(f"Added monitoring for {config.url}")
        return monitoring_id
    
    async def start_monitoring(self, monitoring_id: str):
        """모니터링 시작"""
        if monitoring_id not in self.monitoring_configs:
            raise ValueError(f"Monitoring {monitoring_id} not found")
        
        if monitoring_id in self.monitoring_tasks:
            self.logger.warning(f"Monitoring {monitoring_id} already running")
            return
        
        config = self.monitoring_configs[monitoring_id]
        task = asyncio.create_task(self._monitoring_loop(monitoring_id, config))
        self.monitoring_tasks[monitoring_id] = task
        
        self.logger.info(f"Started monitoring {monitoring_id}")
    
    async def stop_monitoring(self, monitoring_id: str):
        """모니터링 중지"""
        if monitoring_id in self.monitoring_tasks:
            task = self.monitoring_tasks[monitoring_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.monitoring_tasks[monitoring_id]
            self.logger.info(f"Stopped monitoring {monitoring_id}")
    
    async def stop_all_monitoring(self):
        """모든 모니터링 중지"""
        tasks = list(self.monitoring_tasks.keys())
        for monitoring_id in tasks:
            await self.stop_monitoring(monitoring_id)
    
    async def _monitoring_loop(self, monitoring_id: str, config: MonitoringConfig):
        """모니터링 루프"""
        while True:
            try:
                # 콘텐츠 체크
                change_event = await self._check_for_changes(config)
                
                if change_event and change_event.change_type != ChangeType.NO_CHANGE:
                    # 이벤트 발행
                    await self.event_bus.publish(change_event)
                    
                    self.logger.info(
                        f"Change detected for {config.url}: {change_event.change_summary}"
                    )
                
                # 대기
                await asyncio.sleep(config.check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error for {monitoring_id}: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기
    
    async def _check_for_changes(self, config: MonitoringConfig) -> Optional[ChangeEvent]:
        """변경 확인"""
        # 현재 콘텐츠 가져오기
        current_content = await self._fetch_content(config.url, config.custom_headers)
        if not current_content:
            return None
        
        # 이전 콘텐츠
        previous = self.content_store.get(config.url)
        
        # 첫 체크
        if not previous:
            self.content_store.save(config.url, current_content)
            return ChangeEvent(
                event_id=self._generate_event_id(),
                url=config.url,
                timestamp=datetime.utcnow(),
                change_type=ChangeType.NEW_CONTENT,
                change_summary="Initial content captured",
                importance_score=0.0,
                notification_priority=NotificationPriority.INFO,
                after_content=current_content
            )
        
        # 변경 확인
        if not self.content_store.has_changed(config.url, current_content):
            return ChangeEvent(
                event_id=self._generate_event_id(),
                url=config.url,
                timestamp=datetime.utcnow(),
                change_type=ChangeType.NO_CHANGE,
                change_summary="No changes detected",
                importance_score=0.0,
                notification_priority=NotificationPriority.INFO
            )
        
        # 변경 분석
        change_event = await self._analyze_changes(
            config,
            previous['content'],
            current_content
        )
        
        # 콘텐츠 저장
        if change_event.importance_score > 0:
            self.content_store.save(config.url, current_content)
        
        return change_event
    
    async def _analyze_changes(
        self,
        config: MonitoringConfig,
        before: str,
        after: str
    ) -> ChangeEvent:
        """변경 분석"""
        # 기본 차이 분석
        diff_result = self._compute_diff(before, after)
        
        # AI 분석 (활성화된 경우)
        ai_analysis = {}
        if config.ai_analysis and self.gemini_client:
            ai_analysis = await self._ai_change_analysis(before, after)
        
        # 중요도 계산
        importance_score = self._calculate_importance(
            diff_result,
            ai_analysis,
            config
        )
        
        # 우선순위 결정
        priority = self._determine_priority(importance_score)
        
        # 변경 요약
        change_summary = self._generate_summary(diff_result, ai_analysis)
        
        # 변경 타입 결정
        change_type = self._determine_change_type(diff_result, ai_analysis)
        
        return ChangeEvent(
            event_id=self._generate_event_id(),
            url=config.url,
            timestamp=datetime.utcnow(),
            change_type=change_type,
            change_summary=change_summary,
            importance_score=importance_score,
            notification_priority=priority,
            before_content=before[:1000],  # 처음 1000자만
            after_content=after[:1000],
            diff_details=diff_result,
            ai_analysis=ai_analysis
        )
    
    async def _ai_change_analysis(
        self,
        before: str,
        after: str
    ) -> Dict[str, Any]:
        """AI 변경 분석"""
        try:
            prompt = self.change_prompt.format_prompt(
                "",  # content는 before/after로 전달
                before=before[:2000],
                after=after[:2000]
            )
            
            response = await self.gemini_client.analyze_content(
                prompt,
                prompt_type='change_analysis'
            )
            
            if response.status == 'success':
                return response.data
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
        
        return {}
    
    def _compute_diff(self, before: str, after: str) -> Dict[str, Any]:
        """차이 계산"""
        # 라인 단위 diff
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        
        differ = difflib.unified_diff(
            before_lines,
            after_lines,
            lineterm=''
        )
        
        added_lines = []
        removed_lines = []
        
        for line in differ:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])
        
        # 변경률 계산
        total_lines = max(len(before_lines), len(after_lines))
        changed_lines = len(added_lines) + len(removed_lines)
        change_ratio = changed_lines / total_lines if total_lines > 0 else 0
        
        return {
            'added_lines': added_lines[:10],  # 처음 10개만
            'removed_lines': removed_lines[:10],
            'added_count': len(added_lines),
            'removed_count': len(removed_lines),
            'change_ratio': change_ratio,
            'size_before': len(before),
            'size_after': len(after),
            'size_diff': len(after) - len(before)
        }
    
    def _calculate_importance(
        self,
        diff_result: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        config: MonitoringConfig
    ) -> float:
        """중요도 계산"""
        importance = 0.0
        
        # 변경률 기반
        change_ratio = diff_result.get('change_ratio', 0)
        importance += change_ratio * 0.3
        
        # AI 분석 기반
        if ai_analysis:
            ai_importance = ai_analysis.get('importance_score', 0)
            if isinstance(ai_importance, (int, float)):
                importance += (ai_importance / 10) * 0.5  # 1-10 스케일 정규화
        
        # 키워드 기반
        if config.keywords:
            added_text = ' '.join(diff_result.get('added_lines', []))
            removed_text = ' '.join(diff_result.get('removed_lines', []))
            
            keyword_found = any(
                keyword.lower() in added_text.lower() or 
                keyword.lower() in removed_text.lower()
                for keyword in config.keywords
            )
            
            if keyword_found:
                importance += 0.2
        
        return min(1.0, importance)  # 0-1 범위
    
    def _determine_priority(self, importance_score: float) -> NotificationPriority:
        """우선순위 결정"""
        if importance_score >= 0.8:
            return NotificationPriority.CRITICAL
        elif importance_score >= 0.6:
            return NotificationPriority.HIGH
        elif importance_score >= 0.4:
            return NotificationPriority.MEDIUM
        elif importance_score >= 0.2:
            return NotificationPriority.LOW
        else:
            return NotificationPriority.INFO
    
    def _determine_change_type(
        self,
        diff_result: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> ChangeType:
        """변경 타입 결정"""
        # AI 분석 우선
        if ai_analysis and 'change_type' in ai_analysis:
            ai_type = ai_analysis['change_type']
            if ai_type == 'major':
                return ChangeType.STRUCTURE_CHANGE
            elif ai_type == 'minor':
                return ChangeType.CONTENT_UPDATE
        
        # 차이 기반 판단
        if diff_result['removed_count'] > 0 and diff_result['added_count'] == 0:
            return ChangeType.REMOVED_CONTENT
        elif diff_result['added_count'] > 0 and diff_result['removed_count'] == 0:
            return ChangeType.NEW_CONTENT
        elif diff_result['change_ratio'] > 0.5:
            return ChangeType.STRUCTURE_CHANGE
        else:
            return ChangeType.CONTENT_UPDATE
    
    def _generate_summary(
        self,
        diff_result: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """변경 요약 생성"""
        # AI 요약 우선
        if ai_analysis and 'change_summary' in ai_analysis:
            return ai_analysis['change_summary']
        
        # 기본 요약
        added = diff_result['added_count']
        removed = diff_result['removed_count']
        
        if added > 0 and removed > 0:
            return f"Content updated: {added} lines added, {removed} lines removed"
        elif added > 0:
            return f"New content added: {added} lines"
        elif removed > 0:
            return f"Content removed: {removed} lines"
        else:
            return "Minor changes detected"
    
    async def _fetch_content(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """콘텐츠 가져오기"""
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        try:
            headers = headers or {}
            async with self._session.get(url, headers=headers) as response:
                return await response.text()
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _generate_monitoring_id(self, url: str) -> str:
        """모니터링 ID 생성"""
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def _generate_event_id(self) -> str:
        """이벤트 ID 생성"""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def subscribe_to_changes(self, callback: Callable, change_type: str = '*'):
        """변경 이벤트 구독"""
        self.event_bus.subscribe(change_type, callback)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """모니터링 상태 조회"""
        return {
            'active_monitors': len(self.monitoring_tasks),
            'monitors': {
                mid: {
                    'url': config.url,
                    'strategy': config.strategy.value,
                    'interval': config.check_interval.total_seconds(),
                    'running': mid in self.monitoring_tasks
                }
                for mid, config in self.monitoring_configs.items()
            },
            'total_events': len(self.event_bus.event_history)
        }
