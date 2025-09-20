from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas import (
    SentimentAnalysisRequest, 
    SentimentAnalysisResponse, 
    BatchSentimentRequest, 
    BatchSentimentResponse
)
from app.services.sentiment_service import SentimentService

router = APIRouter()


@router.post("/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = SentimentService(db)
    result = await service.analyze_sentiment(request.text, request.content_id)
    return result


@router.post("/batch", response_model=BatchSentimentResponse)
async def batch_analyze_sentiment(
    request: BatchSentimentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    service = SentimentService(db)
    result = await service.batch_analyze_sentiment(request.texts, background_tasks)
    return result


@router.get("/history/{content_id}")
async def get_sentiment_history(
    content_id: str,
    limit: Optional[int] = 10,
    db: Session = Depends(get_db)
):
    service = SentimentService(db)
    history = await service.get_sentiment_history(content_id, limit)
    return history


@router.get("/stats")
async def get_sentiment_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = SentimentService(db)
    stats = await service.get_sentiment_statistics(start_date, end_date)
    return stats