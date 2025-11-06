"""
ABSA 분석 라우터

속성 기반 감성 분석을 수행하는 API 엔드포인트입니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db import get_db, ABSAAnalysis
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

# Optional: use shared pagination schema if available
try:
    from shared.schemas import PaginationMeta as SharedPaginationMeta  # type: ignore
except Exception:
    SharedPaginationMeta = None  # Fallback defined below


class PaginationMeta(BaseModel):
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)


# If shared PaginationMeta exists, alias to it to keep one definition
if SharedPaginationMeta is not None:
    PaginationMeta = SharedPaginationMeta  # type: ignore


class AspectSentiment(BaseModel):
    sentiment_score: float
    sentiment_label: str
    confidence: float


class OverallSentiment(BaseModel):
    score: float
    label: str


class AnalyzeResponse(BaseModel):
    analysis_id: str
    content_id: str
    text_preview: str
    aspects_analyzed: List[str]
    aspect_sentiments: Dict[str, AspectSentiment]
    overall_sentiment: OverallSentiment
    confidence: float
    analyzed_at: str


class HistoryItem(BaseModel):
    id: str
    aspects: List[str]
    aspect_sentiments: Dict[str, AspectSentiment]
    overall_sentiment: float | Dict[str, Any]
    confidence: float
    analyzed_at: Optional[str] = None


class HistoryResponse(BaseModel):
    content_id: str
    analyses: List[HistoryItem]
    total: int
    limit: int
    pagination: PaginationMeta


router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_absa(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> AnalyzeResponse:
    """
    속성 기반 감성 분석 수행
    
    텍스트와 속성 리스트를 받아 각 속성별 감성을 분석합니다.
    
    Args:
        request: {
            "text": str,
            "aspects": List[str] (optional),
            "content_id": str (optional)
        }
        db: 데이터베이스 세션
        
    Returns:
        속성별 감성 분석 결과
    """
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # 속성 리스트 (제공되지 않으면 기본값 사용)
    aspects = request.get("aspects", ["수익률", "안정성", "관리비용", "서비스"])
    content_id = request.get("content_id", str(uuid.uuid4()))
    
    # 속성별 감성 분석 (실제로는 ML 모델 사용)
    aspect_sentiments: Dict[str, AspectSentiment] = {}
    for aspect in aspects:
        # 간단한 규칙 기반 분석 (데모용)
        sentiment_score = _analyze_aspect_sentiment(text, aspect)
        # 결정론적 신뢰도: |score| 기반 (0.5 ~ 1.0)
        aspect_confidence = 0.5 + 0.5 * min(1.0, abs(sentiment_score))
        aspect_sentiments[aspect] = AspectSentiment(
            sentiment_score=sentiment_score,
            sentiment_label=_get_sentiment_label(sentiment_score),
            confidence=round(aspect_confidence, 3),
        )
    
    # 전체 감성 점수 계산
    overall_sentiment = sum(
        asp.sentiment_score for asp in aspect_sentiments.values()
    ) / len(aspect_sentiments) if aspect_sentiments else 0
    
    # 결과 저장
    # 전체 신뢰도: 속성별 |score| 평균 기반 (0.5 ~ 1.0)
    if aspect_sentiments:
        mean_abs = sum(abs(v.sentiment_score) for v in aspect_sentiments.values()) / len(aspect_sentiments)
        overall_confidence = 0.5 + 0.5 * min(1.0, mean_abs)
    else:
        overall_confidence = 0.5

    analysis = ABSAAnalysis(
        content_id=content_id,
        text=text[:1000],  # 텍스트 길이 제한
        aspects=aspects,
        aspect_sentiments={k: v.dict() for k, v in aspect_sentiments.items()},
        overall_sentiment=overall_sentiment,
        confidence_score=round(overall_confidence, 3)
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return AnalyzeResponse(
        analysis_id=analysis.id,
        content_id=content_id,
        text_preview=text[:200],
        aspects_analyzed=aspects,
        aspect_sentiments=aspect_sentiments,
        overall_sentiment=OverallSentiment(score=overall_sentiment, label=_get_sentiment_label(overall_sentiment)),
        confidence=analysis.confidence_score,
        analyzed_at=datetime.now().isoformat(),
    )


@router.get("/history/{content_id}", response_model=HistoryResponse)
async def get_analysis_history(
    content_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> HistoryResponse:
    """
    특정 컨텐츠의 ABSA 분석 히스토리 조회
    
    Args:
        content_id: 컨텐츠 ID
        limit: 조회할 최대 개수
        db: 데이터베이스 세션
        
    Returns:
        분석 히스토리 목록
    """
    analyses = db.query(ABSAAnalysis).filter(
        ABSAAnalysis.content_id == content_id
    ).order_by(ABSAAnalysis.created_at.desc()).limit(limit).all()

    items: List[HistoryItem] = [
        HistoryItem(
            id=analysis.id,
            aspects=analysis.aspects,
            aspect_sentiments={k: AspectSentiment(**v) for k, v in (analysis.aspect_sentiments or {}).items()},
            overall_sentiment=analysis.overall_sentiment,
            confidence=analysis.confidence_score,
            analyzed_at=analysis.created_at.isoformat() if analysis.created_at else None,
        )
        for analysis in analyses
    ]

    return HistoryResponse(
        content_id=content_id,
        analyses=items,
        total=len(items),
        limit=limit,
        pagination=PaginationMeta(total=len(items), limit=limit, offset=0),
    )


@router.post("/batch")
async def batch_analyze(
    requests: List[Dict[str, Any]],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    배치 ABSA 분석
    
    여러 텍스트를 한 번에 분석합니다.
    
    Args:
        requests: 분석 요청 리스트
        db: 데이터베이스 세션
        
    Returns:
        배치 분석 결과
    """
    results = []
    success_count = 0
    error_count = 0
    
    for req in requests:
        try:
            result = await analyze_absa(req, db)
            results.append(result.dict() if hasattr(result, "dict") else result)
            success_count += 1
        except Exception as e:
            error_count += 1
            results.append({
                "error": str(e),
                "text_preview": req.get("text", "")[:100]
            })
    
    return {
        "results": results,
        "total_processed": len(requests),
        "success_count": success_count,
        "error_count": error_count
    }


def _analyze_aspect_sentiment(text: str, aspect: str) -> float:
    """
    속성별 감성 점수 계산 (간단한 규칙 기반)
    
    실제 환경에서는 트랜스포머 기반 모델을 사용합니다.
    """
    text_lower = text.lower()
    aspect_lower = aspect.lower()
    
    # 긍정/부정 키워드 (속성별로 다르게 적용 가능)
    positive_keywords = ["좋다", "훌륭", "만족", "우수", "높은", "안정", "저렴"]
    negative_keywords = ["나쁘다", "불만", "부족", "높다", "비싸다", "불안"]
    
    score = 0.0
    
    # 속성 언급 확인
    if aspect_lower in text_lower:
        # 속성 주변 텍스트에서 감성 분석
        for keyword in positive_keywords:
            if keyword in text_lower:
                score += 0.3
        
        for keyword in negative_keywords:
            if keyword in text_lower:
                score -= 0.3
    else:
        # 속성이 언급되지 않은 경우 중립
        score = 0.0
    
    # 점수 정규화 (-1 ~ 1)
    return max(-1.0, min(1.0, score))


def _get_sentiment_label(score: float) -> str:
    """
    감성 점수를 레이블로 변환
    """
    if score > 0.3:
        return "positive"
    elif score < -0.3:
        return "negative"
    else:
        return "neutral"
