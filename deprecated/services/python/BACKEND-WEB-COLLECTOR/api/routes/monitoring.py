"""
모니터링 관련 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import timedelta

from ..models import (
    MonitoringRequest,
    MonitoringResponse,
    MonitoringStatusResponse,
    ChangeHistoryResponse,
    ChangeEvent,
    ResponseStatus
)
from ..dependencies import get_authenticated_system
from hybrid_crawler_main import HybridCrawlerSystem

router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["Monitoring"]
)


@router.post("/start", response_model=MonitoringResponse)
async def start_monitoring(
    request: MonitoringRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> MonitoringResponse:
    """
    웹페이지 모니터링 시작
    
    지정된 URL의 변경사항을 주기적으로 모니터링합니다.
    """
    try:
        from change_detection_v2 import MonitoringConfig, MonitoringStrategy
        from datetime import datetime
        
        # 모니터링 설정 생성
        config = MonitoringConfig(
            url=str(request.url),
            strategy=MonitoringStrategy[request.strategy.value.upper()],
            check_interval=timedelta(minutes=request.check_interval_minutes),
            keywords=request.keywords or [],
            notification_threshold=request.notification_threshold,
            ai_analysis=request.ai_analysis
        )
        
        # 모니터링 시작
        monitoring_id = await system.orchestrator.change_detector.add_monitoring(
            config,
            start_immediately=True
        )
        
        # 다음 체크 시간 계산
        next_check = datetime.utcnow() + config.check_interval
        
        return MonitoringResponse(
            status=ResponseStatus.SUCCESS,
            message="Monitoring started successfully",
            monitoring_id=monitoring_id,
            url=str(request.url),
            strategy=request.strategy,
            next_check=next_check,
            is_active=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.get("/{monitoring_id}", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    monitoring_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> MonitoringStatusResponse:
    """
    모니터링 상태 조회
    
    특정 모니터링 작업의 현재 상태를 조회합니다.
    """
    try:
        # 모니터링 설정 확인
        config = system.orchestrator.change_detector.monitoring_configs.get(monitoring_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitoring {monitoring_id} not found"
            )
        
        # 활성 상태 확인
        is_active = monitoring_id in system.orchestrator.change_detector.monitoring_tasks
        
        # 최근 변경 이벤트
        events = system.orchestrator.change_detector.event_bus.event_history
        relevant_events = [e for e in events if e.url == config.url]
        last_change = relevant_events[-1].to_dict() if relevant_events else None
        
        return MonitoringStatusResponse(
            status=ResponseStatus.SUCCESS,
            message="Monitoring status retrieved",
            monitoring_id=monitoring_id,
            url=config.url,
            is_active=is_active,
            changes_detected=len(relevant_events),
            last_change=last_change
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{monitoring_id}/stop")
async def stop_monitoring(
    monitoring_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    모니터링 중지
    
    특정 모니터링 작업을 중지합니다.
    """
    try:
        await system.orchestrator.change_detector.stop_monitoring(monitoring_id)
        
        return {
            "status": "success",
            "message": f"Monitoring {monitoring_id} stopped",
            "monitoring_id": monitoring_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/{monitoring_id}/history", response_model=ChangeHistoryResponse)
async def get_change_history(
    monitoring_id: str,
    limit: int = 10,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> ChangeHistoryResponse:
    """
    변경 히스토리 조회
    
    모니터링 중 감지된 변경사항 히스토리를 조회합니다.
    """
    try:
        # 모니터링 설정 확인
        config = system.orchestrator.change_detector.monitoring_configs.get(monitoring_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitoring {monitoring_id} not found"
            )
        
        # 이벤트 히스토리 조회
        all_events = system.orchestrator.change_detector.event_bus.event_history
        
        # URL로 필터링
        relevant_events = [
            e for e in all_events 
            if e.url == config.url
        ]
        
        # 최신 순으로 정렬하고 제한
        relevant_events.sort(key=lambda x: x.timestamp, reverse=True)
        limited_events = relevant_events[:limit]
        
        # ChangeEvent 모델로 변환
        changes = [
            ChangeEvent(
                event_id=e.event_id,
                url=e.url,
                timestamp=e.timestamp,
                change_type=e.change_type.value,
                importance_score=e.importance_score,
                change_summary=e.change_summary,
                notification_priority=e.notification_priority.value,
                diff_details=e.diff_details,
                ai_analysis=e.ai_analysis
            )
            for e in limited_events
        ]
        
        return ChangeHistoryResponse(
            status=ResponseStatus.SUCCESS,
            message="Change history retrieved",
            url=config.url,
            total_changes=len(relevant_events),
            changes=changes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/list/active")
async def list_active_monitoring(
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> dict:
    """
    활성 모니터링 목록
    
    현재 활성화된 모든 모니터링 작업 목록을 조회합니다.
    """
    try:
        monitoring_list = []
        
        for monitoring_id, config in system.orchestrator.change_detector.monitoring_configs.items():
            is_active = monitoring_id in system.orchestrator.change_detector.monitoring_tasks
            
            if is_active:
                monitoring_list.append({
                    "monitoring_id": monitoring_id,
                    "url": config.url,
                    "strategy": config.strategy.value,
                    "interval_minutes": config.check_interval.total_seconds() / 60,
                    "keywords": config.keywords
                })
        
        return {
            "status": "success",
            "total": len(monitoring_list),
            "monitoring": monitoring_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
