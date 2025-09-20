from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas import TrendAnalysisRequest, TrendAnalysisResponse, TrendItem
from app.services.trend_service import TrendService

router = APIRouter()


@router.post("/analyze", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = TrendService(db)
    result = await service.analyze_trends(
        period=request.period,
        entity=request.entity,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return result


@router.get("/entity/{entity}")
async def get_entity_trends(
    entity: str,
    period: str = "weekly",
    limit: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    service = TrendService(db)
    trends = await service.get_entity_trends(entity, period, limit)
    return trends


@router.get("/popular")
async def get_popular_trends(
    period: str = "daily",
    limit: Optional[int] = 10,
    db: Session = Depends(get_db)
):
    service = TrendService(db)
    trends = await service.get_popular_trends(period, limit)
    return trends


@router.get("/keywords")
async def get_trending_keywords(
    period: str = "daily",
    limit: Optional[int] = 20,
    db: Session = Depends(get_db)
):
    service = TrendService(db)
    keywords = await service.get_trending_keywords(period, limit)
    return keywords