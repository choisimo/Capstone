from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db, AlertRule
from app.schemas import (
    AlertRule as AlertRuleSchema,
    AlertRuleCreate,
    AlertRuleUpdate,
    TestRuleRequest,
    TestRuleResponse
)
from app.services.rule_service import RuleService

router = APIRouter()

@router.get("/", response_model=List[AlertRuleSchema])
async def get_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all alert rules with optional filtering"""
    rule_service = RuleService(db)
    return rule_service.get_rules(
        skip=skip,
        limit=limit,
        is_active=is_active,
        alert_type=alert_type,
        severity=severity
    )

@router.get("/{rule_id}", response_model=AlertRuleSchema)
async def get_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific alert rule by ID"""
    rule_service = RuleService(db)
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    return rule

@router.post("/", response_model=AlertRuleSchema)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert rule"""
    rule_service = RuleService(db)
    
    try:
        # Validate rule conditions
        rule_service.validate_rule_conditions(rule_data.alert_type, rule_data.conditions)
        
        # Create the rule
        rule = rule_service.create_rule(rule_data)
        
        return rule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert rule: {str(e)}"
        )

@router.put("/{rule_id}", response_model=AlertRuleSchema)
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing alert rule"""
    rule_service = RuleService(db)
    
    # Check if rule exists
    existing_rule = rule_service.get_rule(rule_id)
    if not existing_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    try:
        # Validate conditions if they're being updated
        if rule_update.conditions is not None:
            alert_type = rule_update.alert_type or existing_rule.alert_type
            rule_service.validate_rule_conditions(alert_type, rule_update.conditions)
        
        # Update the rule
        updated_rule = rule_service.update_rule(rule_id, rule_update)
        
        return updated_rule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert rule: {str(e)}"
        )

@router.patch("/{rule_id}/toggle")
async def toggle_rule_status(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Toggle the active status of an alert rule"""
    rule_service = RuleService(db)
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    try:
        updated_rule = rule_service.toggle_rule_status(rule_id)
        return {
            "message": f"Rule {'activated' if updated_rule.is_active else 'deactivated'} successfully",
            "rule": updated_rule
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle rule status: {str(e)}"
        )

@router.delete("/{rule_id}")
async def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete an alert rule"""
    rule_service = RuleService(db)
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    try:
        # Check if rule has active alerts
        active_alerts_count = rule_service.get_active_alerts_count(rule_id)
        if active_alerts_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete rule with {active_alerts_count} active alerts. Resolve alerts first."
            )
        
        rule_service.delete_rule(rule_id)
        return {"message": "Alert rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert rule: {str(e)}"
        )

@router.post("/{rule_id}/test", response_model=TestRuleResponse)
async def test_alert_rule(
    rule_id: int,
    test_request: TestRuleRequest,
    db: Session = Depends(get_db)
):
    """Test an alert rule with validation data"""
    rule_service = RuleService(db)
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    try:
        # Test the rule
        result = rule_service.test_rule(rule_id, test_request.validation_data)
        
        return TestRuleResponse(
            would_trigger=result["would_trigger"],
            matched_conditions=result["matched_conditions"],
            message_preview=result["message_preview"],
            estimated_recipients=result["estimated_recipients"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test rule: {str(e)}"
        )

@router.get("/{rule_id}/alerts")
async def get_rule_alerts(
    rule_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all alerts for a specific rule"""
    rule_service = RuleService(db)
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    return rule_service.get_rule_alerts(rule_id, skip, limit, status)

@router.get("/{rule_id}/stats")
async def get_rule_stats(
    rule_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific rule"""
    rule_service = RuleService(db)
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert rule with ID {rule_id} not found"
        )
    
    return rule_service.get_rule_stats(rule_id, days)

@router.post("/validate-conditions")
async def validate_rule_conditions(
    alert_type: str,
    conditions: dict,
    db: Session = Depends(get_db)
):
    """Validate rule conditions without creating a rule"""
    rule_service = RuleService(db)
    
    try:
        is_valid, errors = rule_service.validate_rule_conditions(alert_type, conditions, return_errors=True)
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "message": "Conditions are valid" if is_valid else "Conditions have errors"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate conditions: {str(e)}"
        )

@router.get("/types/available")
async def get_available_rule_types():
    """Get available alert rule types and their required conditions"""
    return {
        "sentiment_threshold": {
            "description": "Trigger when sentiment score crosses a threshold",
            "required_conditions": ["threshold", "operator", "metric"],
            "example": {
                "threshold": 0.5,
                "operator": "less_than",  # less_than, greater_than, equals
                "metric": "compound_score"  # compound_score, positive, negative, neutral
            }
        },
        "volume_spike": {
            "description": "Trigger when data volume increases significantly",
            "required_conditions": ["spike_percentage", "time_window"],
            "example": {
                "spike_percentage": 50,  # 50% increase
                "time_window": "1h"  # 1 hour, 1d, 1w
            }
        },
        "keyword_mention": {
            "description": "Trigger when specific keywords are mentioned",
            "required_conditions": ["keywords", "frequency"],
            "example": {
                "keywords": ["pension", "retirement", "crisis"],
                "frequency": 10  # mentions per hour
            }
        },
        "trend_change": {
            "description": "Trigger when sentiment trend changes direction",
            "required_conditions": ["trend_direction", "duration"],
            "example": {
                "trend_direction": "negative",  # positive, negative, neutral
                "duration": "2h"  # minimum duration
            }
        },
        "custom": {
            "description": "Custom rule with flexible conditions",
            "required_conditions": ["expression"],
            "example": {
                "expression": "sentiment_score < 0.3 AND volume > 100"
            }
        }
    }