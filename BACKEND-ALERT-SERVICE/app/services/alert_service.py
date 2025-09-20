from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.db import AlertRule, Alert, AlertHistory, get_db
from app.schemas import (
    AlertCreate, AlertUpdate, TriggerAlertRequest, BulkAlertRequest, 
    AlertStats, AlertDashboard, AlertSeverity, AlertStatus, AlertType
)

logger = logging.getLogger(__name__)

class AlertService:
    
    @staticmethod
    def create_alert(db: Session, alert_data: AlertCreate) -> Alert:
        """Create a new alert"""
        try:
            db_alert = Alert(**alert_data.dict())
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            logger.info(f"Created alert {db_alert.id} with severity {db_alert.severity}")
            return db_alert
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert: {str(e)}")
            raise

    @staticmethod
    def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()

    @staticmethod
    def get_alerts(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Alert]:
        """Get alerts with filtering"""
        query = db.query(Alert)
        
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if start_date:
            query = query.filter(Alert.created_at >= start_date)
        if end_date:
            query = query.filter(Alert.created_at <= end_date)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_alert(db: Session, alert_id: int, alert_data: AlertUpdate) -> Optional[Alert]:
        """Update an alert"""
        try:
            db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not db_alert:
                return None
                
            update_data = alert_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_alert, field, value)
                
            db_alert.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_alert)
            logger.info(f"Updated alert {alert_id}")
            return db_alert
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update alert {alert_id}: {str(e)}")
            raise

    @staticmethod
    def delete_alert(db: Session, alert_id: int) -> bool:
        """Delete an alert"""
        try:
            db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not db_alert:
                return False
                
            db.delete(db_alert)
            db.commit()
            logger.info(f"Deleted alert {alert_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete alert {alert_id}: {str(e)}")
            raise

    @staticmethod
    def trigger_alert(db: Session, trigger_data: TriggerAlertRequest) -> Alert:
        """Trigger a new alert based on rule and data"""
        try:
            # Get the alert rule
            rule = db.query(AlertRule).filter(AlertRule.id == trigger_data.rule_id).first()
            if not rule or not rule.is_active:
                raise ValueError(f"Alert rule {trigger_data.rule_id} not found or inactive")
            
            # Check cooldown period
            if AlertService._is_in_cooldown(db, rule.id):
                logger.info(f"Alert rule {rule.id} is in cooldown period, skipping")
                return None
            
            # Evaluate conditions
            if not AlertService._evaluate_conditions(rule.conditions, trigger_data.data):
                logger.info(f"Conditions not met for rule {rule.id}, skipping alert")
                return None
            
            # Create alert
            alert_data = AlertCreate(
                rule_id=rule.id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=trigger_data.title or f"Alert from rule: {rule.name}",
                message=trigger_data.message or AlertService._generate_message(rule, trigger_data.data),
                data=trigger_data.data,
                source_data_id=trigger_data.source_data_id,
                status=AlertStatus.PENDING
            )
            
            alert = AlertService.create_alert(db, alert_data)
            
            # Create history entry
            AlertService._create_history_entry(db, alert.id, "created", "Alert triggered by rule")
            
            logger.info(f"Successfully triggered alert {alert.id} from rule {rule.id}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {str(e)}")
            raise

    @staticmethod
    def _is_in_cooldown(db: Session, rule_id: int) -> bool:
        """Check if rule is in cooldown period"""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return False
            
        cooldown_start = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
        recent_alert = db.query(Alert).filter(
            and_(
                Alert.rule_id == rule_id,
                Alert.created_at >= cooldown_start
            )
        ).first()
        
        return recent_alert is not None

    @staticmethod
    def _evaluate_conditions(conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate alert conditions against provided data"""
        try:
            for condition_key, condition_value in conditions.items():
                if condition_key not in data:
                    return False
                    
                data_value = data[condition_key]
                
                # Handle different condition types
                if isinstance(condition_value, dict):
                    # Threshold conditions
                    if "threshold" in condition_value:
                        operator = condition_value.get("operator", "gte")
                        threshold = condition_value["threshold"]
                        
                        if operator == "gte" and data_value < threshold:
                            return False
                        elif operator == "lte" and data_value > threshold:
                            return False
                        elif operator == "eq" and data_value != threshold:
                            return False
                        elif operator == "gt" and data_value <= threshold:
                            return False
                        elif operator == "lt" and data_value >= threshold:
                            return False
                else:
                    # Direct value comparison
                    if data_value != condition_value:
                        return False
                        
            return True
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False

    @staticmethod
    def _generate_message(rule: AlertRule, data: Dict[str, Any]) -> str:
        """Generate alert message based on rule and data"""
        template = rule.notification_template or "Alert triggered for rule: {rule_name}"
        
        template_vars = {
            "rule_name": rule.name,
            "alert_type": rule.alert_type,
            "severity": rule.severity,
            **data
        }
        
        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}, using default message")
            return f"Alert triggered for rule: {rule.name}"

    @staticmethod
    def _create_history_entry(db: Session, alert_id: int, action: str, details: str):
        """Create alert history entry"""
        try:
            history = AlertHistory(
                alert_id=alert_id,
                action=action,
                details=details,
                created_at=datetime.utcnow()
            )
            db.add(history)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to create history entry: {str(e)}")

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, resolution_note: Optional[str] = None) -> Optional[Alert]:
        """Resolve an alert"""
        alert = AlertService.get_alert(db, alert_id)
        if not alert:
            return None
            
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        # Create history entry
        details = f"Alert resolved. {resolution_note}" if resolution_note else "Alert resolved"
        AlertService._create_history_entry(db, alert_id, "resolved", details)
        
        return alert

    @staticmethod
    def dismiss_alert(db: Session, alert_id: int, dismissal_note: Optional[str] = None) -> Optional[Alert]:
        """Dismiss an alert"""
        alert = AlertService.get_alert(db, alert_id)
        if not alert:
            return None
            
        alert.status = AlertStatus.DISMISSED
        alert.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        # Create history entry
        details = f"Alert dismissed. {dismissal_note}" if dismissal_note else "Alert dismissed"
        AlertService._create_history_entry(db, alert_id, "dismissed", details)
        
        return alert

    @staticmethod
    def get_alert_stats(db: Session) -> AlertStats:
        """Get alert statistics"""
        total_alerts = db.query(Alert).count()
        active_alerts = db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE).count()
        pending_alerts = db.query(Alert).filter(Alert.status == AlertStatus.PENDING).count()
        resolved_alerts = db.query(Alert).filter(Alert.status == AlertStatus.RESOLVED).count()
        
        # Recent alerts (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = db.query(Alert).filter(Alert.created_at >= last_24h).count()
        
        # Severity breakdown
        severity_stats = {}
        for severity in AlertSeverity:
            count = db.query(Alert).filter(Alert.severity == severity).count()
            severity_stats[severity.value] = count
            
        return AlertStats(
            total_alerts=total_alerts,
            active_alerts=active_alerts,
            pending_alerts=pending_alerts,
            resolved_alerts=resolved_alerts,
            recent_alerts=recent_alerts,
            severity_breakdown=severity_stats
        )

    @staticmethod
    def get_alert_dashboard(db: Session) -> AlertDashboard:
        """Get alert dashboard data"""
        stats = AlertService.get_alert_stats(db)
        
        # Recent alerts
        recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()
        
        # Top alert types
        alert_type_stats = {}
        for alert_type in AlertType:
            count = db.query(Alert).filter(Alert.alert_type == alert_type).count()
            alert_type_stats[alert_type.value] = count
        
        return AlertDashboard(
            stats=stats,
            recent_alerts=recent_alerts,
            alert_type_breakdown=alert_type_stats
        )

    @staticmethod
    def bulk_update_alerts(db: Session, request: BulkAlertRequest) -> Dict[str, Any]:
        """Bulk update multiple alerts"""
        try:
            updated_count = 0
            failed_alerts = []
            
            for alert_id in request.alert_ids:
                try:
                    if request.action == "resolve":
                        alert = AlertService.resolve_alert(db, alert_id, request.note)
                    elif request.action == "dismiss":
                        alert = AlertService.dismiss_alert(db, alert_id, request.note)
                    elif request.action == "delete":
                        success = AlertService.delete_alert(db, alert_id)
                        if success:
                            updated_count += 1
                        else:
                            failed_alerts.append(alert_id)
                        continue
                    else:
                        failed_alerts.append(alert_id)
                        continue
                        
                    if alert:
                        updated_count += 1
                    else:
                        failed_alerts.append(alert_id)
                        
                except Exception as e:
                    logger.error(f"Failed to update alert {alert_id}: {str(e)}")
                    failed_alerts.append(alert_id)
            
            return {
                "success": True,
                "updated_count": updated_count,
                "failed_alerts": failed_alerts,
                "total_requested": len(request.alert_ids)
            }
            
        except Exception as e:
            logger.error(f"Bulk update failed: {str(e)}")
            raise