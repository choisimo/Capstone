from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas import ReportRequest, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    result = await service.generate_report(request, background_tasks)
    return result


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[str] = None,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    reports = await service.list_reports(report_type, limit, offset)
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    success = await service.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    format: str = "json",
    db: Session = Depends(get_db)
):
    service = ReportService(db)
    file_response = await service.download_report(report_id, format)
    return file_response