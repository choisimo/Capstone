from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
from fastapi import BackgroundTasks
from app.db import Report
from app.schemas import ReportRequest, ReportResponse


class ReportService:
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_report(self, request: ReportRequest, background_tasks: BackgroundTasks) -> ReportResponse:
        report_content = await self._generate_report_content(request)
        
        report = Report(
            title=request.title,
            report_type=request.report_type,
            content=json.dumps(report_content),
            parameters=json.dumps(request.parameters),
            created_by="system"
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return ReportResponse(
            report_id=report.id,
            title=report.title,
            report_type=report.report_type,
            content=report_content,
            created_at=report.created_at,
            download_url=f"/api/v1/reports/{report.id}/download"
        )
    
    async def list_reports(self, report_type: Optional[str] = None, 
                          limit: int = 10, offset: int = 0) -> List[ReportResponse]:
        query = self.db.query(Report).filter(Report.is_active == True)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        reports = query.offset(offset).limit(limit).all()
        
        return [
            ReportResponse(
                report_id=report.id,
                title=report.title,
                report_type=report.report_type,
                content=json.loads(report.content),
                created_at=report.created_at,
                download_url=f"/api/v1/reports/{report.id}/download"
            )
            for report in reports
        ]
    
    async def get_report(self, report_id: int) -> Optional[ReportResponse]:
        report = self.db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            return None
        
        return ReportResponse(
            report_id=report.id,
            title=report.title,
            report_type=report.report_type,
            content=json.loads(report.content),
            created_at=report.created_at,
            download_url=f"/api/v1/reports/{report.id}/download"
        )
    
    async def delete_report(self, report_id: int) -> bool:
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            return False
        
        report.is_active = False
        self.db.commit()
        return True
    
    async def download_report(self, report_id: int, format: str = "json"):
        report = await self.get_report(report_id)
        
        if not report:
            return None
        
        if format == "json":
            return report.content
        else:
            return {"error": "Format not supported"}
    
    async def _generate_report_content(self, request: ReportRequest) -> Dict[str, Any]:
        if request.report_type == "sentiment":
            return await self._generate_sentiment_report(request)
        elif request.report_type == "trend":
            return await self._generate_trend_report(request)
        elif request.report_type == "summary":
            return await self._generate_summary_report(request)
        else:
            return {"error": "Unknown report type"}
    
    async def _generate_sentiment_report(self, request: ReportRequest) -> Dict[str, Any]:
        return {
            "type": "sentiment_analysis",
            "title": request.title,
            "generated_at": datetime.now().isoformat(),
            "summary": "Sentiment analysis report",
            "data": {
                "positive_sentiment": 45.2,
                "negative_sentiment": 23.1,
                "neutral_sentiment": 31.7,
                "total_analyzed": 1250
            }
        }
    
    async def _generate_trend_report(self, request: ReportRequest) -> Dict[str, Any]:
        return {
            "type": "trend_analysis",
            "title": request.title,
            "generated_at": datetime.now().isoformat(),
            "summary": "Trend analysis report",
            "data": {
                "trending_up": ["pension fund A", "retirement planning"],
                "trending_down": ["pension crisis"],
                "stable": ["general pension news"]
            }
        }
    
    async def _generate_summary_report(self, request: ReportRequest) -> Dict[str, Any]:
        return {
            "type": "summary",
            "title": request.title,
            "generated_at": datetime.now().isoformat(),
            "summary": "Comprehensive summary report",
            "data": {
                "key_findings": [
                    "Positive sentiment increased by 15%",
                    "Pension fund A trending positively",
                    "Overall market sentiment stable"
                ]
            }
        }