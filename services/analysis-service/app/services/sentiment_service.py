from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from transformers import pipeline
import asyncio
from app.db import SentimentAnalysis
from app.schemas import SentimentAnalysisRequest, SentimentAnalysisResponse


class SentimentService:
    def __init__(self, db: Session):
        self.db = db
        self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                          model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    
    async def analyze_sentiment(self, text: str, content_id: Optional[str] = None) -> SentimentAnalysisResponse:
        if not content_id:
            content_id = str(uuid.uuid4())
        
        result = self.sentiment_analyzer(text)[0]
        
        sentiment_score = self._convert_to_numeric_score(result['label'], result['score'])
        sentiment_label = self._normalize_label(result['label'])
        
        analysis = SentimentAnalysis(
            content_id=content_id,
            text=text,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=result['score'],
            model_version="twitter-roberta-base-sentiment-latest-v1"
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return SentimentAnalysisResponse(
            content_id=content_id,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=result['score'],
            model_version="twitter-roberta-base-sentiment-latest-v1",
            analysis_id=analysis.id
        )
    
    async def batch_analyze_sentiment(self, requests: List[SentimentAnalysisRequest], background_tasks) -> Dict[str, Any]:
        results = []
        success_count = 0
        error_count = 0
        
        for request in requests:
            try:
                result = await self.analyze_sentiment(request.text, request.content_id)
                results.append(result)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing sentiment analysis: {e}")
        
        return {
            "results": results,
            "total_processed": len(requests),
            "success_count": success_count,
            "error_count": error_count
        }
    
    async def get_sentiment_history(self, content_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        analyses = self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.content_id == content_id
        ).order_by(SentimentAnalysis.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": analysis.id,
                "sentiment_score": analysis.sentiment_score,
                "sentiment_label": analysis.sentiment_label,
                "confidence": analysis.confidence,
                "created_at": analysis.created_at
            }
            for analysis in analyses
        ]
    
    async def get_sentiment_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        query = self.db.query(SentimentAnalysis)
        
        if start_date:
            query = query.filter(SentimentAnalysis.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(SentimentAnalysis.created_at <= datetime.fromisoformat(end_date))
        
        analyses = query.all()
        
        if not analyses:
            return {"total": 0, "average_sentiment": 0, "distribution": {}}
        
        total = len(analyses)
        avg_sentiment = sum(a.sentiment_score for a in analyses) / total
        
        distribution = {}
        for analysis in analyses:
            label = analysis.sentiment_label
            distribution[label] = distribution.get(label, 0) + 1
        
        return {
            "total": total,
            "average_sentiment": avg_sentiment,
            "distribution": distribution,
            "period": {"start": start_date, "end": end_date}
        }
    
    def _convert_to_numeric_score(self, label: str, confidence: float) -> float:
        if "POSITIVE" in label.upper():
            return confidence
        elif "NEGATIVE" in label.upper():
            return -confidence
        else:
            return 0.0
    
    def _normalize_label(self, label: str) -> str:
        if "POSITIVE" in label.upper():
            return "positive"
        elif "NEGATIVE" in label.upper():
            return "negative"
        else:
            return "neutral"