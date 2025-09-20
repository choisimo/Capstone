from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db import get_db, Alert, AlertRule, AlertHistory
from app.schemas import (
    Alert as AlertSchema,
    AlertCreate,
    AlertUpdate,
    AlertWithRule,
    TriggerAlertRequest,
    BulkAlertRequest,
    AlertResponse,
    BulkAlertResponse,
    AlertStats,
    AlertDashboard
)
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/", response_model=List[AlertSchema])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    rule_id: Optional[int] = Query(None),
    source_service: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all alerts with optional filtering"""
    alert_service = AlertService(db)
    return alert_service.get_alerts(
        skip=skip,
        limit=limit,
        status=status,
        severity=severity,
        rule_id=rule_id,
        source_service=source_service,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{alert_id}", response_model=AlertWithRule)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID"""
    alert_service = AlertService(db)
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    return alert

@router.post("/", response_model=AlertResponse)
async def create_alert(alert_data: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert"""
    alert_service = AlertService(db)
    notification_service = NotificationService(db)
    
    try:
        # Create the alert
        alert = alert_service.create_alert(alert_data)
        
        # Send notifications
        await notification_service.send_alert_notifications(alert)
        
        return AlertResponse(
            success=True,
            message="Alert created successfully",
            alert_id=alert.id,
            data={"alert": alert}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/trigger", response_model=AlertResponse)
async def trigger_alert(request: TriggerAlertRequest, db: Session = Depends(get_db)):
    """Trigger an alert based on rule conditions"""
    alert_service = AlertService(db)
    notification_service = NotificationService(db)
    
    try:
        # Check if rule should trigger
        should_trigger, message = alert_service.evaluate_rule(
            request.rule_id,
            request.triggered_data,
            request.actual_value
        )
        
        if not should_trigger:
            return AlertResponse(
                success=False,
                message="Rule conditions not met",
                data={"evaluation": message}
            )
        
        # Create alert
        alert_data = AlertCreate(
            rule_id=request.rule_id,
            title=f"Alert from {request.source_service}",
            message=request.custom_message or message,
            severity=alert_service.get_rule_severity(request.rule_id),
            triggered_data=request.triggered_data,
            actual_value=request.actual_value,
            source_service=request.source_service,
            source_data_id=request.source_data_id
        )
        
        alert = alert_service.create_alert(alert_data)
        
        # Send notifications
        await notification_service.send_alert_notifications(alert)
        
        return AlertResponse(
            success=True,
            message="Alert triggered and notifications sent",
            alert_id=alert.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/bulk-trigger", response_model=BulkAlertResponse)
async def bulk_trigger_alerts(request: BulkAlertRequest, db: Session = Depends(get_db)):
    """Trigger multiple alerts in bulk"""
    alert_service = AlertService(db)
    notification_service = NotificationService(db)
    
    created_alerts = []
    errors = []
    
    for alert_request in request.alerts:
        try:
            # Check if rule should trigger
            should_trigger, message = alert_service.evaluate_rule(
                alert_request.rule_id,
                alert_request.triggered_data,
                alert_request.actual_value
            )
            
            if should_trigger:
                alert_data = AlertCreate(
                    rule_id=alert_request.rule_id,
                    title=f"Alert from {alert_request.source_service}",
                    message=alert_request.custom_message or message,
                    severity=alert_service.get_rule_severity(alert_request.rule_id),
                    triggered_data=alert_request.triggered_data,
                    actual_value=alert_request.actual_value,
                    source_service=alert_request.source_service,
                    source_data_id=alert_request.source_data_id
                )
                
                alert = alert_service.create_alert(alert_data)
                created_alerts.append(alert.id)
                
                # Send notifications (async)
                await notification_service.send_alert_notifications(alert)
                
        except Exception as e:
            errors.append(f"Rule {alert_request.rule_id}: {str(e)}")
    
    return BulkAlertResponse(
        success=len(errors) == 0,
        created_count=len(created_alerts),
        failed_count=len(errors),
        created_alerts=created_alerts,
        errors=errors
    )

@router.patch("/{alert_id}", response_model=AlertSchema)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Update an alert (acknowledge, resolve, etc.)"""
    alert_service = AlertService(db)
    
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    try:
        updated_alert = alert_service.update_alert(alert_id, alert_update, user_id)
        return updated_alert
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert_service = AlertService(db)
    
    try:
        alert = alert_service.acknowledge_alert(alert_id, user_id)
        return {"message": "Alert acknowledged successfully", "alert": alert}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    user_id: str = Query(...),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    alert_service = AlertService(db)
    
    try:
        alert = alert_service.resolve_alert(alert_id, user_id, notes)
        return {"message": "Alert resolved successfully", "alert": alert}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    alert_service = AlertService(db)
    
    if not alert_service.get_alert(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    try:
        alert_service.delete_alert(alert_id)
        return {"message": "Alert deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/overview", response_model=AlertStats)
async def get_alert_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get alert statistics overview"""
    alert_service = AlertService(db)
    return alert_service.get_alert_stats(days)

@router.get("/dashboard/summary", response_model=AlertDashboard)
async def get_alert_dashboard(db: Session = Depends(get_db)):
    """Get comprehensive alert dashboard data"""
    alert_service = AlertService(db)
    return alert_service.get_dashboard_data()

@router.get("/{alert_id}/history")
async def get_alert_history(alert_id: int, db: Session = Depends(get_db)):
    """Get history for a specific alert"""
    alert_service = AlertService(db)
    
    if not alert_service.get_alert(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    return alert_service.get_alert_history(alert_id)