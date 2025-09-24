"""
시스템 관련 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime, timedelta

from ..models import (
    SystemHealthResponse,
    SystemStatisticsResponse,
    ResponseStatus,
    TaskRequest,
    TaskResponse,
    TaskStatusResponse,
    ScheduleRequest,
    ScheduleResponse
)
from ..dependencies import get_optional_auth_system, get_authenticated_system
from hybrid_crawler_main import HybridCrawlerSystem
from orchestrator.orchestrator import TaskType, TaskPriority
from orchestrator.scheduler import ScheduleType

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System"]
)


@router.get("/health", response_model=SystemHealthResponse)
async def health_check(
    system: HybridCrawlerSystem = Depends(get_optional_auth_system)
) -> SystemHealthResponse:
    """
    시스템 헬스 체크
    
    시스템의 현재 상태를 확인합니다.
    """
    try:
        # 컴포넌트 상태 확인
        components = {}
        
        # 오케스트레이터
        if system.orchestrator:
            components["orchestrator"] = "healthy"
        
        # 워크플로우 엔진
        if system.workflow_engine:
            components["workflow_engine"] = "healthy"
        
        # 스케줄러
        if system.scheduler and system.scheduler._running:
            components["scheduler"] = "healthy"
        else:
            components["scheduler"] = "stopped"
        
        # 이벤트 버스
        if system.event_bus and system.event_bus._running:
            components["event_bus"] = "healthy"
        else:
            components["event_bus"] = "stopped"
        
        # 전체 시스템 상태
        all_healthy = all(status == "healthy" for status in components.values())
        
        return SystemHealthResponse(
            status=ResponseStatus.SUCCESS,
            message="System is operational",
            healthy=all_healthy,
            components=components,
            uptime=0.0,  # TODO: 실제 uptime 계산
            version="1.0.0"
        )
        
    except Exception as e:
        return SystemHealthResponse(
            status=ResponseStatus.ERROR,
            message=f"Health check failed: {str(e)}",
            healthy=False,
            components={},
            uptime=0.0,
            version="1.0.0"
        )


@router.get("/statistics", response_model=SystemStatisticsResponse)
async def get_statistics(
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> SystemStatisticsResponse:
    """
    시스템 통계 조회
    
    시스템 사용 통계를 조회합니다.
    """
    try:
        stats = system.get_statistics()
        
        return SystemStatisticsResponse(
            status=ResponseStatus.SUCCESS,
            message="Statistics retrieved",
            statistics=stats,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/task", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> TaskResponse:
    """
    작업 생성
    
    새로운 작업을 생성하고 큐에 추가합니다.
    """
    try:
        # TaskType enum 변환
        task_type_map = {
            "scrape": TaskType.SCRAPE,
            "monitor": TaskType.MONITOR,
            "analyze": TaskType.ANALYZE,
            "learn": TaskType.LEARN,
            "evaluate": TaskType.EVALUATE,
            "report": TaskType.REPORT
        }
        
        task_type = task_type_map.get(request.task_type.lower())
        if not task_type:
            raise ValueError(f"Invalid task type: {request.task_type}")
        
        # TaskPriority enum 변환
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND
        }
        
        priority = priority_map.get(request.priority.value.lower(), TaskPriority.MEDIUM)
        
        # 작업 생성
        task_id = await system.orchestrator.create_task(
            task_type=task_type,
            config=request.config,
            priority=priority,
            dependencies=request.dependencies,
            metadata=request.metadata
        )
        
        return TaskResponse(
            status=ResponseStatus.SUCCESS,
            message="Task created",
            task_id=task_id,
            task_type=request.task_type,
            task_status="pending"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> TaskStatusResponse:
    """
    작업 상태 조회
    
    작업의 현재 상태를 조회합니다.
    """
    try:
        task_dict = system.orchestrator.get_task_status(task_id)
        
        if not task_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # Task 객체 직접 조회
        task = system.orchestrator.task_queue.get_task(task_id)
        
        return TaskStatusResponse(
            status=ResponseStatus.SUCCESS,
            message="Task status retrieved",
            task_id=task_id,
            task_type=task_dict['task_type'],
            status=task_dict['status'],
            created_at=task_dict['created_at'],
            started_at=task_dict.get('started_at'),
            completed_at=task_dict.get('completed_at'),
            result=task.result if task else None,
            error=task.error if task else None,
            retry_count=task_dict['retry_count']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/schedule", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> ScheduleResponse:
    """
    스케줄 작업 생성
    
    정기적으로 실행될 작업을 스케줄링합니다.
    """
    try:
        # 액션 함수 생성
        async def scheduled_action():
            # 실제 작업 실행
            task_type_map = {
                "scrape": TaskType.SCRAPE,
                "analyze": TaskType.ANALYZE,
                "report": TaskType.REPORT
            }
            
            task_type = task_type_map.get(request.task_type.lower())
            if task_type:
                await system.orchestrator.create_task(
                    task_type=task_type,
                    config=request.task_config
                )
        
        # 스케줄 타입별 처리
        if request.schedule_type == ScheduleType.INTERVAL:
            interval = request.schedule_config.get("interval", 3600)
            schedule_id = system.scheduler.schedule_interval(
                name=request.name,
                action=scheduled_action,
                interval=interval,
                action_args=request.task_config
            )
            
        elif request.schedule_type == ScheduleType.DAILY:
            hour = request.schedule_config.get("hour", 0)
            minute = request.schedule_config.get("minute", 0)
            schedule_id = system.scheduler.schedule_daily(
                name=request.name,
                action=scheduled_action,
                hour=hour,
                minute=minute,
                action_args=request.task_config
            )
            
        elif request.schedule_type == ScheduleType.CRON:
            cron_expr = request.schedule_config.get("cron", "0 * * * *")
            schedule_id = system.scheduler.schedule_cron(
                name=request.name,
                action=scheduled_action,
                cron_expr=cron_expr,
                action_args=request.task_config
            )
            
        else:
            raise ValueError(f"Unsupported schedule type: {request.schedule_type}")
        
        # 다음 실행 시간 조회
        job = system.scheduler.get_job(schedule_id)
        
        return ScheduleResponse(
            status=ResponseStatus.SUCCESS,
            message="Schedule created",
            schedule_id=schedule_id,
            name=request.name,
            next_run=job.next_run if job else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.delete("/schedule/{schedule_id}")
async def cancel_schedule(
    schedule_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    스케줄 작업 취소
    """
    try:
        success = system.scheduler.cancel_job(schedule_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Schedule {schedule_id} cancelled",
            "schedule_id": schedule_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel schedule: {str(e)}"
        )
