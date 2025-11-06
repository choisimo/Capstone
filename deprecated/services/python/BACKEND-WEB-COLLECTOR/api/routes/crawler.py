"""
크롤링 관련 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import asyncio

from ..models import (
    ScrapeRequest,
    ScrapeResponse,
    TemplateRequest,
    TemplateResponse,
    ResponseStatus,
    ErrorResponse
)
from ..dependencies import get_authenticated_system
from hybrid_crawler_main import HybridCrawlerSystem

router = APIRouter(
    prefix="/api/v1/crawler",
    tags=["Crawler"]
)


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> ScrapeResponse:
    """
    웹페이지 스크래핑
    
    웹페이지에서 콘텐츠를 추출합니다.
    """
    try:
        # 작업 생성
        from orchestrator.orchestrator import TaskType, TaskPriority
        
        task_id = await system.orchestrator.create_task(
            TaskType.SCRAPE,
            {
                "url": str(request.url),
                "prompt": request.prompt,
                "strategy": request.strategy.value,
                "target_fields": request.target_fields,
                "use_cache": request.use_cache,
                "custom_headers": request.custom_headers
            },
            priority=TaskPriority.HIGH
        )
        
        # 비동기 실행이므로 task_id만 반환
        return ScrapeResponse(
            status=ResponseStatus.SUCCESS,
            message="Scraping task created",
            task_id=task_id,
            metadata={
                "url": str(request.url),
                "strategy": request.strategy.value
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@router.get("/scrape/{task_id}", response_model=ScrapeResponse)
async def get_scrape_result(
    task_id: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> ScrapeResponse:
    """
    스크래핑 결과 조회
    
    작업 ID로 스크래핑 결과를 조회합니다.
    """
    try:
        # 작업 상태 확인
        task_status = system.orchestrator.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        if task_status['status'] == 'completed':
            # 결과 가져오기
            task = system.orchestrator.task_queue.get_task(task_id)
            
            return ScrapeResponse(
                status=ResponseStatus.SUCCESS,
                message="Scraping completed",
                task_id=task_id,
                data=task.result.data if task and task.result else None,
                metadata=task.result.metadata if task and task.result else {}
            )
            
        elif task_status['status'] == 'failed':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping task failed"
            )
            
        else:
            # 아직 진행 중
            return ScrapeResponse(
                status=ResponseStatus.PENDING,
                message=f"Task is {task_status['status']}",
                task_id=task_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/template/learn", response_model=TemplateResponse)
async def learn_template(
    request: TemplateRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> TemplateResponse:
    """
    웹페이지 구조 학습
    
    웹페이지의 구조를 학습하여 추출 템플릿을 생성합니다.
    """
    try:
        # HTML 샘플이 없으면 페이지 가져오기
        if not request.html_sample:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(str(request.url)) as response:
                    html = await response.text()
        else:
            html = request.html_sample
        
        # 템플릿 학습
        template = await system.orchestrator.template_learner.learn(
            str(request.url),
            html,
            request.target_fields
        )
        
        return TemplateResponse(
            status=ResponseStatus.SUCCESS,
            message="Template learned successfully",
            template_id=template.template_id,
            domain=template.domain,
            confidence=template.confidence,
            selectors=template.selectors,
            version=template.version
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template learning failed: {str(e)}"
        )


@router.get("/template/{domain}", response_model=TemplateResponse)
async def get_template(
    domain: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> TemplateResponse:
    """
    도메인 템플릿 조회
    
    특정 도메인의 추출 템플릿을 조회합니다.
    """
    try:
        templates = system.orchestrator.template_learner.get_domain_templates(domain)
        
        if not templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No template found for domain: {domain}"
            )
        
        # 가장 최신 템플릿 반환
        template = templates[-1]
        
        return TemplateResponse(
            status=ResponseStatus.SUCCESS,
            message="Template found",
            template_id=template.template_id,
            domain=template.domain,
            confidence=template.confidence,
            selectors=template.selectors,
            version=template.version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
