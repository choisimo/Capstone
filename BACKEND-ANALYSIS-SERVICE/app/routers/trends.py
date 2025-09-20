from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db import get_db
from app.schemas import TrendAnalysisRequest, TrendAnalysisResponse, TrendItem
from app.services.trend_service import TrendService
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        trend_service = TrendService()
        
        trends = await trend_service.analyze_trends(
            db,
            time_period=request.time_period,
            topic=request.topic,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        trend_items = [
            TrendItem(**trend)
            for trend in trends
        ]
        
        return TrendAnalysisResponse(
            trends=trend_items,
            time_period=request.time_period,
            analyzed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top", response_model=List[TrendItem])
async def get_top_trends(
    limit: int = 10,
    time_period: str = "7d",
    db: Session = Depends(get_db)
):
    try:
        trend_service = TrendService()
        
        trends = await trend_service.analyze_trends(
            db,
            time_period=time_period
        )
        
        return [
            TrendItem(**trend)
            for trend in trends[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Failed to get top trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{topic}")
async def get_historical_trends(
    topic: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    try:
        trend_service = TrendService()
        
        historical_data = await trend_service.get_historical_trends(
            db,
            topic=topic,
            days=days
        )
        
        return historical_data
        
    except Exception as e:
        logger.error(f"Failed to get historical trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare")
async def compare_trends(
    topics: List[str],
    time_period: str = "7d",
    db: Session = Depends(get_db)
):
    try:
        if len(topics) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 topics can be compared")
        
        trend_service = TrendService()
        
        comparison_data = []
        for topic in topics:
            trends = await trend_service.analyze_trends(
                db,
                time_period=time_period,
                topic=topic
            )
            
            if trends:
                comparison_data.append({
                    "topic": topic,
                    "data": trends[0] if trends else None
                })
        
        return comparison_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging")
async def get_emerging_trends(
    threshold: float = 0.5,
    time_period: str = "24h",
    db: Session = Depends(get_db)
):
    try:
        trend_service = TrendService()
        
        trends = await trend_service.analyze_trends(
            db,
            time_period=time_period
        )
        
        # Filter for emerging trends (high growth rate)
        emerging = [
            TrendItem(**trend)
            for trend in trends
            if trend["growth_rate"] > threshold
        ]
        
        return emerging
        
    except Exception as e:
        logger.error(f"Failed to get emerging trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))