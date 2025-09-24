from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from collections import defaultdict
from app.db import TrendAnalysis, SentimentAnalysis
from app.schemas import TrendAnalysisResponse, TrendItem


class TrendService:
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_trends(self, period: str, entity: Optional[str] = None, 
                           start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> TrendAnalysisResponse:
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.created_at >= start_date,
            SentimentAnalysis.created_at <= end_date
        )
        
        if entity:
            query = query.filter(SentimentAnalysis.text.contains(entity))
        
        analyses = query.all()
        
        trend_data = self._calculate_trend(analyses, period)
        
        return TrendAnalysisResponse(
            period=period,
            entity=entity or "all",
            trend_direction=trend_data["direction"],
            trend_strength=trend_data["strength"],
            data_points=trend_data["data_points"],
            summary=trend_data["summary"]
        )
    
    async def get_entity_trends(self, entity: str, period: str = "weekly", limit: int = 30) -> List[Dict[str, Any]]:
        trends = self.db.query(TrendAnalysis).filter(
            TrendAnalysis.entity == entity,
            TrendAnalysis.period == period
        ).order_by(TrendAnalysis.analysis_date.desc()).limit(limit).all()
        
        return [
            {
                "date": trend.analysis_date,
                "sentiment_trend": trend.sentiment_trend,
                "volume_trend": trend.volume_trend,
                "keywords": json.loads(trend.keywords) if trend.keywords else [],
                "confidence": trend.confidence
            }
            for trend in trends
        ]
    
    async def get_popular_trends(self, period: str = "daily", limit: int = 10) -> List[Dict[str, Any]]:
        trends = self.db.query(TrendAnalysis).filter(
            TrendAnalysis.period == period
        ).order_by(TrendAnalysis.volume_trend.desc()).limit(limit).all()
        
        return [
            {
                "entity": trend.entity,
                "sentiment_trend": trend.sentiment_trend,
                "volume_trend": trend.volume_trend,
                "keywords": json.loads(trend.keywords) if trend.keywords else []
            }
            for trend in trends
        ]
    
    async def get_trending_keywords(self, period: str = "daily", limit: int = 20) -> List[Dict[str, Any]]:
        trends = self.db.query(TrendAnalysis).filter(
            TrendAnalysis.period == period,
            TrendAnalysis.analysis_date >= datetime.now() - timedelta(days=7)
        ).all()
        
        keyword_counts = defaultdict(int)
        for trend in trends:
            if trend.keywords:
                keywords = json.loads(trend.keywords)
                for keyword in keywords:
                    keyword_counts[keyword] += trend.volume_trend
        
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {"keyword": keyword, "score": score}
            for keyword, score in sorted_keywords
        ]
    
    def _calculate_trend(self, analyses: List, period: str) -> Dict[str, Any]:
        if not analyses:
            return {
                "direction": "stable",
                "strength": 0.0,
                "data_points": [],
                "summary": "No data available"
            }
        
        grouped_data = defaultdict(list)
        for analysis in analyses:
            date_key = analysis.created_at.strftime("%Y-%m-%d")
            grouped_data[date_key].append(analysis)
        
        data_points = []
        sentiment_scores = []
        
        for date_key, day_analyses in grouped_data.items():
            avg_sentiment = sum(a.sentiment_score for a in day_analyses) / len(day_analyses)
            volume = len(day_analyses)
            
            sentiment_scores.append(avg_sentiment)
            data_points.append(TrendItem(
                date=datetime.strptime(date_key, "%Y-%m-%d"),
                sentiment_score=avg_sentiment,
                volume=volume,
                keywords=self._extract_keywords(day_analyses)
            ))
        
        if len(sentiment_scores) < 2:
            direction = "stable"
            strength = 0.0
        else:
            trend_change = sentiment_scores[-1] - sentiment_scores[0]
            if trend_change > 0.1:
                direction = "increasing"
            elif trend_change < -0.1:
                direction = "decreasing"
            else:
                direction = "stable"
            
            strength = abs(trend_change)
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        summary = f"Average sentiment: {avg_sentiment:.2f}, Trend: {direction}"
        
        return {
            "direction": direction,
            "strength": strength,
            "data_points": data_points,
            "summary": summary
        }
    
    def _extract_keywords(self, analyses: List, limit: int = 5) -> List[str]:
        all_text = " ".join([a.text for a in analyses])
        words = all_text.lower().split()
        
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were"}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        word_counts = defaultdict(int)
        for word in filtered_words:
            word_counts[word] += 1
        
        return [word for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:limit]]