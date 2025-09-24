"""
워크플로우 관련 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models import (
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStatusResponse,
    ResponseStatus
)
from ..dependencies import get_authenticated_system
from hybrid_crawler_main import HybridCrawlerSystem
from orchestrator.workflow_engine import WorkflowBuilder

router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["Workflow"]
)


@router.post("/create", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> WorkflowResponse:
    """
    워크플로우 생성 및 실행
    
    복잡한 작업 시퀀스를 워크플로우로 정의하고 실행합니다.
    """
    try:
        # 워크플로우 빌더 생성
        builder = WorkflowBuilder(
            name=request.name,
            description=request.description or ""
        )
        
        # 초기 컨텍스트 설정
        if request.initial_context:
            builder.set_context(request.initial_context)
        
        # 스텝 추가
        step_ids = {}
        for step in request.steps:
            if step.type == "action":
                # 액션 스텝
                step_id = builder.add_action(
                    name=step.name,
                    action=lambda ctx, cfg=step.config: cfg,  # 실제 액션은 config에서 처리
                    config=step.config
                )
                step_ids[step.name] = step_id
                
            # 다른 스텝 타입들도 추가 가능
            # elif step.type == "condition":
            #     ...
        
        # 스텝 연결
        for step in request.steps:
            if step.name in step_ids and step.next_steps:
                for next_step in step.next_steps:
                    if next_step in step_ids:
                        builder.connect(step_ids[step.name], step_ids[next_step])
        
        # 시작 스텝 설정
        if request.start_step and request.start_step in step_ids:
            builder.set_start(step_ids[request.start_step])
        
        # 워크플로우 빌드
        workflow = builder.build()
        
        # 워크플로우 실행
        result = await system.workflow_engine.execute_workflow(
            workflow,
            request.initial_context
        )
        
        return WorkflowResponse(
            status=ResponseStatus.SUCCESS,
            message="Workflow executed successfully",
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            execution_status=workflow.status.value,
            results=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> WorkflowStatusResponse:
    """
    워크플로우 상태 조회
    
    실행 중인 워크플로우의 현재 상태를 조회합니다.
    """
    try:
        status_dict = system.workflow_engine.get_workflow_status(workflow_id)
        
        if not status_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowStatusResponse(
            status=ResponseStatus.SUCCESS,
            message="Workflow status retrieved",
            workflow_id=workflow_id,
            name=status_dict['name'],
            status=status_dict['status'],
            current_step=status_dict.get('current_step'),
            steps_completed=status_dict['steps_completed'],
            total_steps=status_dict['total_steps'],
            started_at=status_dict.get('started_at'),
            completed_at=status_dict.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    워크플로우 일시정지
    """
    try:
        await system.workflow_engine.pause_workflow(workflow_id)
        
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} paused",
            "workflow_id": workflow_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause workflow: {str(e)}"
        )


@router.post("/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    워크플로우 재개
    """
    try:
        await system.workflow_engine.resume_workflow(workflow_id)
        
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} resumed",
            "workflow_id": workflow_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow: {str(e)}"
        )


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    워크플로우 취소
    """
    try:
        await system.workflow_engine.cancel_workflow(workflow_id)
        
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} cancelled",
            "workflow_id": workflow_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}"
        )
