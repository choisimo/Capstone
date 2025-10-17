"""
OSINT Collection Planning Service

OSINT 수집 계획 서비스:
- 소스 우선순위 결정
- 수집 일정 최적화
- 리소스 할당 계산
- 의존성 그래프 생성
- Orchestrator와 통합
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import json
import httpx

logger = logging.getLogger(__name__)


class SourcePriority(str, Enum):
    """소스 우선순위"""
    CRITICAL = "critical"  # 필수
    HIGH = "high"  # 높음
    MEDIUM = "medium"  # 중간
    LOW = "low"  # 낮음


class PlanStatus(str, Enum):
    """계획 상태"""
    DRAFT = "draft"  # 초안
    APPROVED = "approved"  # 승인됨
    EXECUTING = "executing"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소


@dataclass
class SourceSpec:
    """수집 소스 사양"""
    source_id: str
    source_type: str  # website, rss, api, social
    url: str
    priority: SourcePriority
    frequency: str  # hourly, daily, weekly
    estimated_time_minutes: int
    dependencies: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class CollectionTask:
    """수집 작업"""
    task_id: str
    source_spec: SourceSpec
    scheduled_time: datetime
    assigned_worker: Optional[str] = None
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Plan:
    """수집 계획"""
    plan_id: str
    title: str
    description: str
    status: PlanStatus
    sources: List[SourceSpec]
    tasks: List[CollectionTask]
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    total_estimated_time: int  # minutes
    resource_requirements: Dict[str, int]


@dataclass
class ExecutionResult:
    """실행 결과"""
    plan_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    start_time: datetime
    end_time: Optional[datetime]
    status: PlanStatus
    task_results: List[Dict[str, Any]] = field(default_factory=list)


class PlanningService:
    """OSINT 수집 계획 서비스"""
    
    # 소스 타입별 기본 설정
    DEFAULT_SOURCE_CONFIG = {
        "website": {"frequency": "daily", "est_time": 10, "priority": "medium"},
        "rss": {"frequency": "hourly", "est_time": 5, "priority": "high"},
        "api": {"frequency": "hourly", "est_time": 3, "priority": "high"},
        "social": {"frequency": "daily", "est_time": 15, "priority": "low"}
    }
    
    # 우선순위별 가중치
    PRIORITY_WEIGHTS = {
        SourcePriority.CRITICAL: 100,
        SourcePriority.HIGH: 75,
        SourcePriority.MEDIUM: 50,
        SourcePriority.LOW: 25
    }
    
    def __init__(self, db: Session, orchestrator_url: Optional[str] = None):
        """
        초기화
        
        Args:
            db: 데이터베이스 세션
            orchestrator_url: Orchestrator 서비스 URL
        """
        self.db = db
        self.orchestrator_url = orchestrator_url or "http://osint-orchestrator:8005"
        self.active_plans: Dict[str, Plan] = {}
    
    async def create_collection_plan(
        self,
        title: str,
        sources: List[Dict[str, Any]],
        start_time: Optional[datetime] = None,
        duration_hours: int = 24,
        optimize: bool = True
    ) -> Plan:
        """
        수집 계획 생성
        
        Args:
            title: 계획 제목
            sources: 소스 목록
            start_time: 시작 시간 (None이면 즉시)
            duration_hours: 지속 시간 (시간)
            optimize: 최적화 여부
            
        Returns:
            Plan: 생성된 계획
        """
        plan_id = str(uuid.uuid4())
        
        if not start_time:
            start_time = datetime.now()
        
        end_time = start_time + timedelta(hours=duration_hours)
        
        # 소스 사양 생성
        source_specs = self._create_source_specs(sources)
        
        # 우선순위 결정
        if optimize:
            source_specs = self._optimize_source_priority(source_specs)
        
        # 수집 작업 생성 및 스케줄링
        tasks = self._schedule_tasks(source_specs, start_time, end_time)
        
        # 의존성 해결
        tasks = self._resolve_dependencies(tasks)
        
        # 리소스 요구사항 계산
        resource_reqs = self._calculate_resource_requirements(tasks)
        
        # 총 예상 시간 계산
        total_time = sum(spec.estimated_time_minutes for spec in source_specs)
        
        plan = Plan(
            plan_id=plan_id,
            title=title,
            description=f"{len(source_specs)}개 소스, {len(tasks)}개 작업",
            status=PlanStatus.DRAFT,
            sources=source_specs,
            tasks=tasks,
            start_time=start_time,
            end_time=end_time,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_estimated_time=total_time,
            resource_requirements=resource_reqs
        )
        
        self.active_plans[plan_id] = plan
        
        logger.info(
            f"계획 생성: {plan_id}, {len(source_specs)}개 소스, "
            f"{len(tasks)}개 작업, 예상 {total_time}분"
        )
        
        return plan
    
    def _create_source_specs(self, sources: List[Dict[str, Any]]) -> List[SourceSpec]:
        """
        소스 사양 생성
        
        Args:
            sources: 소스 정보 목록
            
        Returns:
            소스 사양 목록
        """
        specs = []
        
        for source in sources:
            source_type = source.get("type", "website")
            config = self.DEFAULT_SOURCE_CONFIG.get(source_type, {})
            
            spec = SourceSpec(
                source_id=source.get("id", str(uuid.uuid4())),
                source_type=source_type,
                url=source["url"],
                priority=SourcePriority(source.get("priority", config.get("priority", "medium"))),
                frequency=source.get("frequency", config.get("frequency", "daily")),
                estimated_time_minutes=source.get("est_time", config.get("est_time", 10)),
                dependencies=source.get("dependencies", []),
                max_retries=source.get("max_retries", 3),
                timeout_seconds=source.get("timeout", 300)
            )
            
            specs.append(spec)
        
        return specs
    
    def _optimize_source_priority(self, specs: List[SourceSpec]) -> List[SourceSpec]:
        """
        소스 우선순위 최적화
        
        기준:
        1. 우선순위 가중치
        2. 업데이트 빈도 (hourly > daily > weekly)
        3. 예상 소요 시간 (짧을수록 우선)
        
        Args:
            specs: 소스 사양 목록
            
        Returns:
            최적화된 소스 사양 목록
        """
        def priority_score(spec: SourceSpec) -> float:
            # 기본 우선순위 점수
            score = self.PRIORITY_WEIGHTS.get(spec.priority, 50)
            
            # 빈도 가산점
            if spec.frequency == "hourly":
                score += 20
            elif spec.frequency == "daily":
                score += 10
            
            # 소요 시간 감점 (짧을수록 우선)
            score -= spec.estimated_time_minutes * 0.1
            
            return score
        
        # 점수 기준 정렬 (높은 순)
        optimized = sorted(specs, key=priority_score, reverse=True)
        
        logger.info(f"{len(specs)}개 소스 우선순위 최적화 완료")
        
        return optimized
    
    def _schedule_tasks(
        self,
        specs: List[SourceSpec],
        start_time: datetime,
        end_time: datetime
    ) -> List[CollectionTask]:
        """
        수집 작업 스케줄링
        
        Args:
            specs: 소스 사양 목록
            start_time: 시작 시간
            end_time: 종료 시간
            
        Returns:
            스케줄된 작업 목록
        """
        tasks = []
        current_time = start_time
        
        for spec in specs:
            # 빈도에 따라 반복 작업 생성
            interval = self._get_interval_minutes(spec.frequency)
            
            task_time = current_time
            while task_time < end_time:
                task = CollectionTask(
                    task_id=f"{spec.source_id}_{task_time.strftime('%Y%m%d%H%M')}",
                    source_spec=spec,
                    scheduled_time=task_time,
                    dependencies=spec.dependencies.copy()
                )
                tasks.append(task)
                
                task_time += timedelta(minutes=interval)
            
            # 다음 소스는 약간의 간격을 두고 시작
            current_time += timedelta(minutes=5)
        
        logger.info(f"{len(tasks)}개 작업 스케줄 완료")
        
        return tasks
    
    def _get_interval_minutes(self, frequency: str) -> int:
        """빈도에 따른 간격(분) 반환"""
        intervals = {
            "hourly": 60,
            "daily": 24 * 60,
            "weekly": 7 * 24 * 60,
            "monthly": 30 * 24 * 60
        }
        return intervals.get(frequency, 24 * 60)
    
    def _resolve_dependencies(self, tasks: List[CollectionTask]) -> List[CollectionTask]:
        """
        작업 의존성 해결
        
        의존성이 있는 작업은 선행 작업 완료 후 실행되도록 조정
        
        Args:
            tasks: 작업 목록
            
        Returns:
            의존성이 해결된 작업 목록
        """
        # 소스 ID별 작업 그룹화
        source_tasks = {}
        for task in tasks:
            source_id = task.source_spec.source_id
            if source_id not in source_tasks:
                source_tasks[source_id] = []
            source_tasks[source_id].append(task)
        
        # 의존성 확인 및 조정
        for task in tasks:
            if task.dependencies:
                # 의존하는 소스의 가장 최근 작업 ID 추가
                resolved_deps = []
                for dep_source_id in task.dependencies:
                    if dep_source_id in source_tasks:
                        # 같은 시간대의 선행 작업 찾기
                        for dep_task in source_tasks[dep_source_id]:
                            if dep_task.scheduled_time <= task.scheduled_time:
                                resolved_deps.append(dep_task.task_id)
                                break
                
                task.dependencies = resolved_deps
        
        logger.info(f"의존성 해결 완료: {sum(1 for t in tasks if t.dependencies)}개 작업에 의존성")
        
        return tasks
    
    def _calculate_resource_requirements(self, tasks: List[CollectionTask]) -> Dict[str, int]:
        """
        리소스 요구사항 계산
        
        Args:
            tasks: 작업 목록
            
        Returns:
            리소스 요구사항 (워커 수, 메모리 등)
        """
        # 동시 실행될 최대 작업 수 계산
        time_slots = {}
        for task in tasks:
            time_key = task.scheduled_time.strftime("%Y-%m-%d %H:%M")
            time_slots[time_key] = time_slots.get(time_key, 0) + 1
        
        max_concurrent = max(time_slots.values()) if time_slots else 1
        
        # 소스 타입별 작업 수
        type_counts = {}
        for task in tasks:
            source_type = task.source_spec.source_type
            type_counts[source_type] = type_counts.get(source_type, 0) + 1
        
        return {
            "min_workers": max(1, max_concurrent // 2),
            "recommended_workers": max_concurrent,
            "max_concurrent_tasks": max_concurrent,
            "estimated_memory_mb": max_concurrent * 512,  # 작업당 512MB 추정
            "source_type_distribution": type_counts
        }
    
    async def execute_plan(self, plan_id: str) -> ExecutionResult:
        """
        계획 실행
        
        Orchestrator에 작업 등록 및 실행 모니터링
        
        Args:
            plan_id: 계획 ID
            
        Returns:
            ExecutionResult: 실행 결과
        """
        plan = self.active_plans.get(plan_id)
        if not plan:
            raise ValueError(f"계획을 찾을 수 없습니다: {plan_id}")
        
        if plan.status != PlanStatus.DRAFT and plan.status != PlanStatus.APPROVED:
            raise ValueError(f"실행할 수 없는 상태입니다: {plan.status}")
        
        plan.status = PlanStatus.EXECUTING
        plan.updated_at = datetime.now()
        
        logger.info(f"계획 실행 시작: {plan_id}")
        
        # Orchestrator에 작업 등록
        registered_tasks = await self._register_tasks_to_orchestrator(plan.tasks)
        
        result = ExecutionResult(
            plan_id=plan_id,
            total_tasks=len(plan.tasks),
            completed_tasks=0,
            failed_tasks=0,
            pending_tasks=len(plan.tasks),
            start_time=datetime.now(),
            end_time=None,
            status=PlanStatus.EXECUTING,
            task_results=registered_tasks
        )
        
        logger.info(f"계획 실행 등록 완료: {len(registered_tasks)}개 작업")
        
        return result
    
    async def _register_tasks_to_orchestrator(
        self,
        tasks: List[CollectionTask]
    ) -> List[Dict[str, Any]]:
        """
        Orchestrator에 작업 등록
        
        Args:
            tasks: 작업 목록
            
        Returns:
            등록된 작업 정보 목록
        """
        registered: List[Dict[str, Any]] = []
        tasks_url = f"{self.orchestrator_url.rstrip('/')}/api/v1/osint/tasks"

        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for task in tasks:
                payload = {
                    "task_type": "collection",
                    "keywords": ["국민연금"],  # TODO: 소스별/플랜별 키워드 연결
                    "sources": [task.source_spec.url],
                    "priority": task.source_spec.priority.value,
                    "metadata": {
                        "plan_task_id": task.task_id,
                        "source_type": task.source_spec.source_type,
                        "scheduled_time": task.scheduled_time.isoformat()
                    },
                    "dependencies": task.dependencies,
                    "timeout_seconds": task.source_spec.timeout_seconds,
                    "expected_results": 0
                }

                try:
                    resp = await client.post(tasks_url, json=payload)
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        task_id = data.get("task_id")
                        registered.append({
                            **payload,
                            "created_task_id": task_id
                        })
                        logger.debug(f"작업 등록 성공: {task.task_id} -> {task_id}")
                    else:
                        text = resp.text
                        logger.error(
                            f"Orchestrator 작업 등록 실패: {task.task_id} status={resp.status_code} body={text}"
                        )
                        registered.append({
                            **payload,
                            "error": f"HTTP {resp.status_code}",
                            "error_body": text
                        })
                except httpx.ConnectError as e:
                    logger.error(f"Orchestrator 연결 실패: {e}")
                    registered.append({**payload, "error": "connect_error", "error_body": str(e)})
                except httpx.TimeoutException as e:
                    logger.error(f"Orchestrator 타임아웃: {e}")
                    registered.append({**payload, "error": "timeout", "error_body": str(e)})
                except Exception as e:
                    logger.exception(f"작업 등록 중 예외: {e}")
                    registered.append({**payload, "error": "exception", "error_body": str(e)})

        return registered
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """계획 조회"""
        return self.active_plans.get(plan_id)
    
    def list_plans(self, status: Optional[PlanStatus] = None) -> List[Plan]:
        """계획 목록 조회"""
        plans = list(self.active_plans.values())
        
        if status:
            plans = [p for p in plans if p.status == status]
        
        return plans
    
    def cancel_plan(self, plan_id: str) -> bool:
        """계획 취소"""
        plan = self.active_plans.get(plan_id)
        if not plan:
            return False
        
        if plan.status in [PlanStatus.COMPLETED, PlanStatus.CANCELLED]:
            return False
        
        plan.status = PlanStatus.CANCELLED
        plan.updated_at = datetime.now()
        
        logger.info(f"계획 취소: {plan_id}")
        return True
