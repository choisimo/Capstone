"""
분석 관련 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models import (
    AnalysisRequest,
    AnalysisResponse,
    ResponseStatus
)
from ..dependencies import get_authenticated_system
from hybrid_crawler_main import HybridCrawlerSystem

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(
    request: AnalysisRequest,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    콘텐츠 분석
    
    텍스트 콘텐츠에 대한 다양한 AI 분석을 수행합니다.
    
    지원 분석 타입:
    - sentiment: 감성 분석
    - absa: Aspect-Based Sentiment Analysis
    - keywords: 키워드 추출
    - summary: 요약
    - news_analysis: 뉴스 분석
    - pension_sentiment: 연금 특화 감성 분석
    """
    try:
        # Gemini 클라이언트로 직접 분석
        response = await system.orchestrator.gemini_client.analyze_content(
            request.content,
            prompt_type=request.analysis_type.value,
            additional_context=request.additional_context
        )
        
        if response.status == "success":
            # 신뢰도 계산
            confidence = response.data.get('confidence', 0.8)
            if 'sentiment_score' in response.data:
                # 감성 점수 기반 신뢰도 조정
                score = abs(response.data['sentiment_score'])
                confidence = min(1.0, score + 0.3)
            
            return AnalysisResponse(
                status=ResponseStatus.SUCCESS,
                message="Analysis completed",
                analysis_type=request.analysis_type,
                result=response.data,
                confidence=confidence
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {response.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )


@router.post("/sentiment", response_model=AnalysisResponse)
async def analyze_sentiment(
    content: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    감성 분석 (간편 메서드)
    
    텍스트의 감성을 분석합니다.
    """
    request = AnalysisRequest(
        content=content,
        analysis_type="sentiment"
    )
    return await analyze_content(request, system)


@router.post("/pension-sentiment", response_model=AnalysisResponse)
async def analyze_pension_sentiment(
    content: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    연금 특화 감성 분석
    
    연금 관련 텍스트의 감성을 전문적으로 분석합니다.
    """
    request = AnalysisRequest(
        content=content,
        analysis_type="pension_sentiment"
    )
    return await analyze_content(request, system)


@router.post("/keywords", response_model=AnalysisResponse)
async def extract_keywords(
    content: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    키워드 추출
    
    텍스트에서 주요 키워드를 추출합니다.
    """
    request = AnalysisRequest(
        content=content,
        analysis_type="keywords"
    )
    return await analyze_content(request, system)


@router.post("/summary", response_model=AnalysisResponse)
async def summarize_content(
    content: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    텍스트 요약
    
    긴 텍스트를 요약합니다.
    """
    request = AnalysisRequest(
        content=content,
        analysis_type="summary"
    )
    return await analyze_content(request, system)


@router.post("/absa", response_model=AnalysisResponse)
async def analyze_aspects(
    content: str,
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> AnalysisResponse:
    """
    Aspect-Based Sentiment Analysis
    
    텍스트의 각 측면별 감성을 분석합니다.
    """
    request = AnalysisRequest(
        content=content,
        analysis_type="absa"
    )
    return await analyze_content(request, system)


@router.post("/batch", response_model=Dict[str, AnalysisResponse])
async def batch_analysis(
    contents: list[str],
    analysis_type: str = "sentiment",
    system: HybridCrawlerSystem = Depends(get_authenticated_system)
) -> Dict[str, AnalysisResponse]:
    """
    배치 분석
    
    여러 텍스트를 일괄 분석합니다.
    """
    try:
        results = {}
        
        # 배치 처리
        for i, content in enumerate(contents[:10]):  # 최대 10개 제한
            try:
                request = AnalysisRequest(
                    content=content,
                    analysis_type=analysis_type
                )
                result = await analyze_content(request, system)
                results[f"item_{i}"] = result
            except Exception as e:
                results[f"item_{i}"] = AnalysisResponse(
                    status=ResponseStatus.ERROR,
                    message=str(e),
                    analysis_type=analysis_type,
                    result={},
                    confidence=0.0
                )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )
