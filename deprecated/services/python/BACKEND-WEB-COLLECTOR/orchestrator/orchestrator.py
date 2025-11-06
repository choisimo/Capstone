"""
메인 오케스트레이터 서비스
전체 크롤링 워크플로우 조정 및 관리
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Phase 1 컴포넌트
from ..scrapegraph_adapter_v2 import ScrapeGraphAIAdapterV2, ScrapeConfig, ScrapeResult
from ..template_learner import TemplateLearner
from ..change_detection_v2 import ChangeDetectionServiceV2, MonitoringConfig, ChangeEvent
from ..change_evaluator import ChangeImportanceEvaluator
from ..gemini_client_v2 import GeminiClientV2

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """작업 유형"""
    SCRAPE = "scrape"
    MONITOR = "monitor"
    ANALYZE = "analyze"
    LEARN = "learn"
    EVALUATE = "evaluate"
    REPORT = "report"


class TaskPriority(Enum):
    """작업 우선순위"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Task:
    """작업 정의"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


class TaskQueue:
    """우선순위 기반 작업 큐"""
    
    def __init__(self):
        self.queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue()
            for priority in TaskPriority
        }
        self.tasks: Dict[str, Task] = {}
    
    async def put(self, task: Task):
        """작업 추가"""
        self.tasks[task.task_id] = task
        await self.queues[task.priority].put(task)
    
    async def get(self) -> Optional[Task]:
        """우선순위별 작업 가져오기"""
        for priority in sorted(TaskPriority, key=lambda p: p.value, reverse=True):
            queue = self.queues[priority]
            if not queue.empty():
                task = await queue.get()
                return task
        return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self.tasks.get(task_id)
    
    def size(self) -> int:
        """전체 큐 크기"""
        return sum(queue.qsize() for queue in self.queues.values())


class CrawlingOrchestrator:
    """
    하이브리드 크롤링 시스템 오케스트레이터
    
    전체 워크플로우를 조정하고 관리하는 중앙 컨트롤러
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        max_workers: int = 10,
        enable_monitoring: bool = True
    ):
        """
        초기화
        
        Args:
            gemini_api_key: Gemini API 키
            max_workers: 최대 동시 작업 수
            enable_monitoring: 모니터링 활성화
        """
        # 컴포넌트 초기화
        self.scraper = ScrapeGraphAIAdapterV2(gemini_api_key)
        self.template_learner = TemplateLearner(gemini_api_key)
        self.change_detector = ChangeDetectionServiceV2(gemini_api_key, enable_ai=True)
        self.evaluator = ChangeImportanceEvaluator(gemini_api_key, domain="pension")
        self.gemini_client = GeminiClientV2(gemini_api_key)
        
        # 작업 관리
        self.task_queue = TaskQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_workers = max_workers
        
        # 모니터링
        self.enable_monitoring = enable_monitoring
        self.monitoring_configs: Dict[str, MonitoringConfig] = {}
        
        # 통계
        self.statistics = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "scrapes_performed": 0,
            "changes_detected": 0,
            "errors": []
        }
        
        # 콜백
        self.task_callbacks: Dict[TaskType, List[Callable]] = {
            task_type: [] for task_type in TaskType
        }
        
        # 실행 상태
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        self.logger = logger
    
    async def start(self):
        """오케스트레이터 시작"""
        if self._running:
            self.logger.warning("Orchestrator already running")
            return
        
        self._running = True
        self.logger.info(f"Starting orchestrator with {self.max_workers} workers")
        
        # 워커 시작
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
        
        # 변경 감지 이벤트 구독
        if self.enable_monitoring:
            self.change_detector.subscribe_to_changes(self._on_change_detected)
        
        # 모니터링 시작
        await self._start_monitoring()
    
    async def stop(self):
        """오케스트레이터 중지"""
        self._running = False
        self.logger.info("Stopping orchestrator")
        
        # 워커 중지
        for task in self._worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        # 모니터링 중지
        await self.change_detector.stop_all_monitoring()
        
        # 실행 중인 작업 취소
        for task_id, task in self.running_tasks.items():
            task.cancel()
        
        await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        self.running_tasks.clear()
    
    async def _worker_loop(self, worker_id: str):
        """워커 루프"""
        self.logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # 작업 가져오기
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                if task:
                    self.logger.info(f"Worker {worker_id} processing {task.task_id}")
                    await self._process_task(task)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    async def _process_task(self, task: Task):
        """작업 처리"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # 의존성 확인
            if not await self._check_dependencies(task):
                task.status = TaskStatus.PENDING
                await self.task_queue.put(task)  # 다시 큐에 추가
                return
            
            # 작업 실행
            result = await self._execute_task(task)
            
            # 성공
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            
            self.statistics["tasks_completed"] += 1
            
            # 콜백 실행
            await self._run_callbacks(task.task_type, task)
            
        except Exception as e:
            # 실패
            self.logger.error(f"Task {task.task_id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            self.statistics["tasks_failed"] += 1
            self.statistics["errors"].append({
                "task_id": task.task_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 재시도 처리
            if task.retry_count < 3:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                await asyncio.sleep(2 ** task.retry_count)  # 지수 백오프
                await self.task_queue.put(task)
    
    async def _execute_task(self, task: Task) -> Any:
        """작업 실행"""
        task_type = task.task_type
        config = task.config
        
        if task_type == TaskType.SCRAPE:
            return await self._execute_scrape(config)
        
        elif task_type == TaskType.MONITOR:
            return await self._execute_monitor(config)
        
        elif task_type == TaskType.ANALYZE:
            return await self._execute_analyze(config)
        
        elif task_type == TaskType.LEARN:
            return await self._execute_learn(config)
        
        elif task_type == TaskType.EVALUATE:
            return await self._execute_evaluate(config)
        
        elif task_type == TaskType.REPORT:
            return await self._execute_report(config)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _execute_scrape(self, config: Dict[str, Any]) -> ScrapeResult:
        """스크래핑 실행"""
        scrape_config = ScrapeConfig(**config)
        result = await self.scraper.scrape(scrape_config)
        
        self.statistics["scrapes_performed"] += 1
        
        # 성공 시 구조 학습 작업 생성
        if result.success:
            await self.create_task(
                TaskType.LEARN,
                {
                    "url": scrape_config.url,
                    "html": result.data.get("html", ""),
                    "target_fields": scrape_config.target_fields
                },
                priority=TaskPriority.LOW
            )
        
        return result
    
    async def _execute_monitor(self, config: Dict[str, Any]) -> str:
        """모니터링 실행"""
        monitoring_config = MonitoringConfig(**config)
        monitoring_id = await self.change_detector.add_monitoring(
            monitoring_config,
            start_immediately=True
        )
        
        self.monitoring_configs[monitoring_id] = monitoring_config
        
        return monitoring_id
    
    async def _execute_analyze(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """분석 실행"""
        content = config.get("content", "")
        prompt_type = config.get("prompt_type", "sentiment")
        
        response = await self.gemini_client.analyze_content(
            content,
            prompt_type=prompt_type
        )
        
        return response.data if response.status == "success" else {}
    
    async def _execute_learn(self, config: Dict[str, Any]) -> Any:
        """구조 학습 실행"""
        url = config.get("url")
        html = config.get("html")
        target_fields = config.get("target_fields")
        
        template = await self.template_learner.learn(url, html, target_fields)
        
        return template.to_dict()
    
    async def _execute_evaluate(self, config: Dict[str, Any]) -> Any:
        """중요도 평가 실행"""
        before = config.get("before_content", "")
        after = config.get("after_content", "")
        metadata = config.get("metadata", {})
        
        score = await self.evaluator.evaluate(before, after, metadata)
        
        return score.to_dict()
    
    async def _execute_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """리포트 생성"""
        report_type = config.get("report_type", "summary")
        
        if report_type == "summary":
            return self.get_statistics()
        elif report_type == "accuracy":
            return self.evaluator.get_accuracy_report()
        else:
            return {"error": "Unknown report type"}
    
    async def _check_dependencies(self, task: Task) -> bool:
        """의존성 확인"""
        for dep_id in task.dependencies:
            dep_task = self.task_queue.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def _on_change_detected(self, event: ChangeEvent):
        """변경 감지 이벤트 핸들러"""
        self.logger.info(f"Change detected: {event.change_summary}")
        self.statistics["changes_detected"] += 1
        
        # 중요도 평가 작업 생성
        if event.before_content and event.after_content:
            await self.create_task(
                TaskType.EVALUATE,
                {
                    "before_content": event.before_content,
                    "after_content": event.after_content,
                    "metadata": event.metadata
                },
                priority=TaskPriority.HIGH
            )
        
        # 분석 작업 생성 (중요한 변경일 경우)
        if event.importance_score > 0.5:
            await self.create_task(
                TaskType.ANALYZE,
                {
                    "content": event.after_content,
                    "prompt_type": "news_analysis"
                },
                priority=TaskPriority.MEDIUM
            )
    
    async def _start_monitoring(self):
        """기본 모니터링 시작"""
        # 설정된 모니터링 구성으로 시작
        for config in self.monitoring_configs.values():
            await self.create_task(
                TaskType.MONITOR,
                config.__dict__,
                priority=TaskPriority.MEDIUM
            )
    
    async def _run_callbacks(self, task_type: TaskType, task: Task):
        """콜백 실행"""
        callbacks = self.task_callbacks.get(task_type, [])
        for callback in callbacks:
            try:
                await callback(task)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    async def create_task(
        self,
        task_type: TaskType,
        config: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        작업 생성
        
        Args:
            task_type: 작업 유형
            config: 작업 설정
            priority: 우선순위
            dependencies: 의존성 작업 ID 리스트
            metadata: 메타데이터
        
        Returns:
            작업 ID
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            config=config,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        await self.task_queue.put(task)
        
        self.statistics["tasks_created"] += 1
        self.logger.info(f"Created task {task_id} ({task_type.value})")
        
        return task_id
    
    def register_callback(self, task_type: TaskType, callback: Callable):
        """작업 완료 콜백 등록"""
        if task_type not in self.task_callbacks:
            self.task_callbacks[task_type] = []
        self.task_callbacks[task_type].append(callback)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        task = self.task_queue.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            **self.statistics,
            "queue_size": self.task_queue.size(),
            "running_tasks": len(self.running_tasks),
            "active_monitors": len(self.monitoring_configs)
        }
    
    async def add_scraping_job(
        self,
        url: str,
        prompt: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> str:
        """스크래핑 작업 추가 (간편 메서드)"""
        return await self.create_task(
            TaskType.SCRAPE,
            {
                "url": url,
                "prompt": prompt
            },
            priority=priority
        )
    
    async def add_monitoring_job(
        self,
        url: str,
        keywords: List[str] = None,
        check_interval_hours: int = 1,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> str:
        """모니터링 작업 추가 (간편 메서드)"""
        from datetime import timedelta
        
        return await self.create_task(
            TaskType.MONITOR,
            {
                "url": url,
                "keywords": keywords or [],
                "check_interval": timedelta(hours=check_interval_hours)
            },
            priority=priority
        )
