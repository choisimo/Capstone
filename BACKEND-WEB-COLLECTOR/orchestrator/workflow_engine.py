"""
워크플로우 엔진
복잡한 작업 시퀀스와 조건부 실행 관리
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StepType(Enum):
    """워크플로우 스텝 타입"""
    ACTION = "action"  # 실행 스텝
    CONDITION = "condition"  # 조건부 분기
    PARALLEL = "parallel"  # 병렬 실행
    LOOP = "loop"  # 반복 실행
    WAIT = "wait"  # 대기
    SUBWORKFLOW = "subworkflow"  # 서브 워크플로우


class WorkflowStatus(Enum):
    """워크플로우 상태"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """스텝 실행 결과"""
    step_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowStep(ABC):
    """워크플로우 스텝 베이스 클래스"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        step_type: StepType,
        config: Dict[str, Any] = None
    ):
        self.step_id = step_id or str(uuid.uuid4())
        self.name = name
        self.step_type = step_type
        self.config = config or {}
        self.next_steps: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """스텝 실행"""
        pass
    
    def add_next(self, step_id: str) -> 'WorkflowStep':
        """다음 스텝 추가"""
        self.next_steps.append(step_id)
        return self


class ActionStep(WorkflowStep):
    """액션 실행 스텝"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        action: Callable,
        config: Dict[str, Any] = None
    ):
        super().__init__(step_id, name, StepType.ACTION, config)
        self.action = action
    
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """액션 실행"""
        start_time = datetime.utcnow()
        
        try:
            # 액션 실행
            if asyncio.iscoroutinefunction(self.action):
                output = await self.action(context, **self.config)
            else:
                output = self.action(context, **self.config)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return StepResult(
                step_id=self.step_id,
                success=True,
                output=output,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Action step {self.name} failed: {e}")
            
            return StepResult(
                step_id=self.step_id,
                success=False,
                output=None,
                error=str(e),
                execution_time=execution_time
            )


class ConditionStep(WorkflowStep):
    """조건부 분기 스텝"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        condition: Callable[[Dict], bool],
        true_branch: str,
        false_branch: str,
        config: Dict[str, Any] = None
    ):
        super().__init__(step_id, name, StepType.CONDITION, config)
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
    
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """조건 평가"""
        try:
            result = self.condition(context)
            next_step = self.true_branch if result else self.false_branch
            
            return StepResult(
                step_id=self.step_id,
                success=True,
                output={"condition_result": result, "next_step": next_step}
            )
            
        except Exception as e:
            logger.error(f"Condition step {self.name} failed: {e}")
            return StepResult(
                step_id=self.step_id,
                success=False,
                output=None,
                error=str(e)
            )


class ParallelStep(WorkflowStep):
    """병렬 실행 스텝"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        parallel_steps: List[str],
        wait_all: bool = True,
        config: Dict[str, Any] = None
    ):
        super().__init__(step_id, name, StepType.PARALLEL, config)
        self.parallel_steps = parallel_steps
        self.wait_all = wait_all
    
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """병렬 실행"""
        return StepResult(
            step_id=self.step_id,
            success=True,
            output={
                "parallel_steps": self.parallel_steps,
                "wait_all": self.wait_all
            }
        )


class LoopStep(WorkflowStep):
    """반복 실행 스텝"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        loop_steps: List[str],
        condition: Callable[[Dict, int], bool],
        max_iterations: int = 100,
        config: Dict[str, Any] = None
    ):
        super().__init__(step_id, name, StepType.LOOP, config)
        self.loop_steps = loop_steps
        self.condition = condition
        self.max_iterations = max_iterations
        self.current_iteration = 0
    
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """반복 조건 평가"""
        try:
            should_continue = self.condition(context, self.current_iteration)
            
            if should_continue and self.current_iteration < self.max_iterations:
                self.current_iteration += 1
                return StepResult(
                    step_id=self.step_id,
                    success=True,
                    output={
                        "continue": True,
                        "iteration": self.current_iteration,
                        "loop_steps": self.loop_steps
                    }
                )
            else:
                return StepResult(
                    step_id=self.step_id,
                    success=True,
                    output={
                        "continue": False,
                        "total_iterations": self.current_iteration
                    }
                )
                
        except Exception as e:
            logger.error(f"Loop step {self.name} failed: {e}")
            return StepResult(
                step_id=self.step_id,
                success=False,
                output=None,
                error=str(e)
            )


class WaitStep(WorkflowStep):
    """대기 스텝"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        duration: float,
        config: Dict[str, Any] = None
    ):
        super().__init__(step_id, name, StepType.WAIT, config)
        self.duration = duration
    
    async def execute(self, context: Dict[str, Any]) -> StepResult:
        """대기"""
        try:
            await asyncio.sleep(self.duration)
            return StepResult(
                step_id=self.step_id,
                success=True,
                output={"waited": self.duration}
            )
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                success=False,
                output=None,
                error=str(e)
            )


@dataclass
class Workflow:
    """워크플로우 정의"""
    workflow_id: str
    name: str
    description: str
    steps: Dict[str, WorkflowStep]
    start_step: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    results: Dict[str, StepResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_step": self.current_step,
            "steps_completed": len(self.results),
            "total_steps": len(self.steps)
        }


class WorkflowBuilder:
    """워크플로우 빌더"""
    
    def __init__(self, name: str, description: str = ""):
        self.workflow_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.start_step: Optional[str] = None
        self.context: Dict[str, Any] = {}
    
    def add_action(
        self,
        name: str,
        action: Callable,
        config: Dict[str, Any] = None,
        step_id: str = None
    ) -> str:
        """액션 스텝 추가"""
        step_id = step_id or str(uuid.uuid4())
        step = ActionStep(step_id, name, action, config)
        self.steps[step_id] = step
        
        if not self.start_step:
            self.start_step = step_id
        
        return step_id
    
    def add_condition(
        self,
        name: str,
        condition: Callable,
        true_branch: str,
        false_branch: str,
        step_id: str = None
    ) -> str:
        """조건 스텝 추가"""
        step_id = step_id or str(uuid.uuid4())
        step = ConditionStep(step_id, name, condition, true_branch, false_branch)
        self.steps[step_id] = step
        
        if not self.start_step:
            self.start_step = step_id
        
        return step_id
    
    def add_parallel(
        self,
        name: str,
        parallel_steps: List[str],
        wait_all: bool = True,
        step_id: str = None
    ) -> str:
        """병렬 스텝 추가"""
        step_id = step_id or str(uuid.uuid4())
        step = ParallelStep(step_id, name, parallel_steps, wait_all)
        self.steps[step_id] = step
        
        if not self.start_step:
            self.start_step = step_id
        
        return step_id
    
    def add_loop(
        self,
        name: str,
        loop_steps: List[str],
        condition: Callable,
        max_iterations: int = 100,
        step_id: str = None
    ) -> str:
        """반복 스텝 추가"""
        step_id = step_id or str(uuid.uuid4())
        step = LoopStep(step_id, name, loop_steps, condition, max_iterations)
        self.steps[step_id] = step
        
        if not self.start_step:
            self.start_step = step_id
        
        return step_id
    
    def add_wait(
        self,
        name: str,
        duration: float,
        step_id: str = None
    ) -> str:
        """대기 스텝 추가"""
        step_id = step_id or str(uuid.uuid4())
        step = WaitStep(step_id, name, duration)
        self.steps[step_id] = step
        
        if not self.start_step:
            self.start_step = step_id
        
        return step_id
    
    def connect(self, from_step: str, to_step: str) -> 'WorkflowBuilder':
        """스텝 연결"""
        if from_step in self.steps:
            self.steps[from_step].add_next(to_step)
        return self
    
    def set_start(self, step_id: str) -> 'WorkflowBuilder':
        """시작 스텝 설정"""
        if step_id in self.steps:
            self.start_step = step_id
        return self
    
    def set_context(self, context: Dict[str, Any]) -> 'WorkflowBuilder':
        """초기 컨텍스트 설정"""
        self.context = context
        return self
    
    def build(self) -> Workflow:
        """워크플로우 빌드"""
        if not self.start_step:
            raise ValueError("Start step not defined")
        
        return Workflow(
            workflow_id=self.workflow_id,
            name=self.name,
            description=self.description,
            steps=self.steps,
            start_step=self.start_step,
            context=self.context
        )


class WorkflowEngine:
    """
    워크플로우 실행 엔진
    
    복잡한 작업 시퀀스를 실행하고 관리
    """
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.workflow_callbacks: List[Callable] = []
        self.logger = logger
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        워크플로우 실행
        
        Args:
            workflow: 실행할 워크플로우
            initial_context: 초기 컨텍스트
        
        Returns:
            실행 결과
        """
        # 워크플로우 등록
        self.workflows[workflow.workflow_id] = workflow
        
        # 상태 업데이트
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        # 컨텍스트 설정
        if initial_context:
            workflow.context.update(initial_context)
        
        try:
            # 실행 시작
            self.logger.info(f"Starting workflow {workflow.name}")
            
            # 실행 태스크 생성
            task = asyncio.create_task(
                self._execute_workflow_internal(workflow)
            )
            self.running_workflows[workflow.workflow_id] = task
            
            # 완료 대기
            result = await task
            
            # 상태 업데이트
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            
            # 콜백 실행
            await self._run_callbacks(workflow)
            
            return result
            
        except asyncio.CancelledError:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.utcnow()
            raise
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            self.logger.error(f"Workflow {workflow.name} failed: {e}")
            raise
            
        finally:
            # 실행 태스크 제거
            if workflow.workflow_id in self.running_workflows:
                del self.running_workflows[workflow.workflow_id]
    
    async def _execute_workflow_internal(
        self,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """워크플로우 내부 실행"""
        current_step_id = workflow.start_step
        visited_steps = set()
        
        while current_step_id:
            # 순환 감지
            if current_step_id in visited_steps:
                self.logger.warning(f"Circular reference detected at step {current_step_id}")
                break
            
            visited_steps.add(current_step_id)
            
            # 스텝 가져오기
            step = workflow.steps.get(current_step_id)
            if not step:
                self.logger.error(f"Step {current_step_id} not found")
                break
            
            # 현재 스텝 업데이트
            workflow.current_step = current_step_id
            self.logger.info(f"Executing step {step.name}")
            
            # 스텝 실행
            result = await self._execute_step(step, workflow)
            workflow.results[current_step_id] = result
            
            # 실패 시 중단
            if not result.success:
                self.logger.error(f"Step {step.name} failed: {result.error}")
                break
            
            # 다음 스텝 결정
            next_step_id = await self._determine_next_step(
                step,
                result,
                workflow
            )
            
            current_step_id = next_step_id
        
        # 최종 결과 반환
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "results": {
                step_id: {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                }
                for step_id, result in workflow.results.items()
            },
            "context": workflow.context
        }
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow
    ) -> StepResult:
        """스텝 실행"""
        # 스텝 타입별 처리
        if step.step_type == StepType.PARALLEL:
            return await self._execute_parallel_step(step, workflow)
        elif step.step_type == StepType.LOOP:
            return await self._execute_loop_step(step, workflow)
        else:
            # 일반 스텝 실행
            return await step.execute(workflow.context)
    
    async def _execute_parallel_step(
        self,
        step: ParallelStep,
        workflow: Workflow
    ) -> StepResult:
        """병렬 스텝 실행"""
        tasks = []
        
        for step_id in step.parallel_steps:
            parallel_step = workflow.steps.get(step_id)
            if parallel_step:
                task = asyncio.create_task(
                    parallel_step.execute(workflow.context)
                )
                tasks.append(task)
        
        if step.wait_all:
            # 모든 태스크 완료 대기
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 첫 번째 완료 대기
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            results = [await task for task in done]
            
            # 나머지 취소
            for task in pending:
                task.cancel()
        
        # 결과 수집
        all_success = all(
            not isinstance(r, Exception) and r.success
            for r in results
        )
        
        return StepResult(
            step_id=step.step_id,
            success=all_success,
            output={"parallel_results": results}
        )
    
    async def _execute_loop_step(
        self,
        step: LoopStep,
        workflow: Workflow
    ) -> StepResult:
        """반복 스텝 실행"""
        loop_results = []
        
        while True:
            # 반복 조건 체크
            loop_result = await step.execute(workflow.context)
            
            if not loop_result.output.get("continue", False):
                break
            
            # 반복 스텝들 실행
            for step_id in step.loop_steps:
                loop_step = workflow.steps.get(step_id)
                if loop_step:
                    result = await loop_step.execute(workflow.context)
                    loop_results.append(result)
        
        return StepResult(
            step_id=step.step_id,
            success=True,
            output={
                "loop_completed": True,
                "iterations": step.current_iteration,
                "results": loop_results
            }
        )
    
    async def _determine_next_step(
        self,
        step: WorkflowStep,
        result: StepResult,
        workflow: Workflow
    ) -> Optional[str]:
        """다음 스텝 결정"""
        # 조건 스텝
        if step.step_type == StepType.CONDITION:
            next_step = result.output.get("next_step")
            return next_step
        
        # 일반 스텝
        if step.next_steps:
            return step.next_steps[0]
        
        return None
    
    async def _run_callbacks(self, workflow: Workflow):
        """콜백 실행"""
        for callback in self.workflow_callbacks:
            try:
                await callback(workflow)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def register_callback(self, callback: Callable):
        """콜백 등록"""
        self.workflow_callbacks.append(callback)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """워크플로우 상태 조회"""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            return workflow.to_dict()
        return None
    
    async def pause_workflow(self, workflow_id: str):
        """워크플로우 일시정지"""
        workflow = self.workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.PAUSED
            
            # 실행 태스크 취소
            if workflow_id in self.running_workflows:
                self.running_workflows[workflow_id].cancel()
    
    async def resume_workflow(self, workflow_id: str):
        """워크플로우 재개"""
        workflow = self.workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            
            # 재실행
            task = asyncio.create_task(
                self._execute_workflow_internal(workflow)
            )
            self.running_workflows[workflow_id] = task
    
    async def cancel_workflow(self, workflow_id: str):
        """워크플로우 취소"""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.utcnow()
            
            # 실행 태스크 취소
            if workflow_id in self.running_workflows:
                self.running_workflows[workflow_id].cancel()
