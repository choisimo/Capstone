from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.db import AlertRule, Alert, get_db
from app.schemas import (
    AlertRuleCreate, AlertRuleUpdate, TestRuleRequest, TestRuleResponse,
    AlertType, AlertSeverity
)

logger = logging.getLogger(__name__)

class RuleService:
    
    @staticmethod
    def create_rule(db: Session, rule_data: AlertRuleCreate) -> AlertRule:
        """Create a new alert rule"""
        try:
            # Validate conditions based on alert type
            RuleService._validate_rule_conditions(rule_data.alert_type, rule_data.conditions)
            
            db_rule = AlertRule(**rule_data.dict())
            db.add(db_rule)
            db.commit()
            db.refresh(db_rule)
            logger.info(f"Created alert rule {db_rule.id}: {db_rule.name}")
            return db_rule
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert rule: {str(e)}")
            raise

    @staticmethod
    def get_rule(db: Session, rule_id: int) -> Optional[AlertRule]:
        """Get alert rule by ID"""
        return db.query(AlertRule).filter(AlertRule.id == rule_id).first()

    @staticmethod
    def get_rules(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        is_active: Optional[bool] = None
    ) -> List[AlertRule]:
        """Get alert rules with filtering"""
        query = db.query(AlertRule)
        
        if alert_type:
            query = query.filter(AlertRule.alert_type == alert_type)
        if severity:
            query = query.filter(AlertRule.severity == severity)
        if is_active is not None:
            query = query.filter(AlertRule.is_active == is_active)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_rule(db: Session, rule_id: int, rule_data: AlertRuleUpdate) -> Optional[AlertRule]:
        """Update an alert rule"""
        try:
            db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not db_rule:
                return None
                
            update_data = rule_data.dict(exclude_unset=True)
            
            # Validate conditions if being updated
            if 'conditions' in update_data and 'alert_type' in update_data:
                RuleService._validate_rule_conditions(update_data['alert_type'], update_data['conditions'])
            elif 'conditions' in update_data:
                RuleService._validate_rule_conditions(db_rule.alert_type, update_data['conditions'])
                
            for field, value in update_data.items():
                setattr(db_rule, field, value)
                
            db_rule.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_rule)
            logger.info(f"Updated alert rule {rule_id}")
            return db_rule
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update alert rule {rule_id}: {str(e)}")
            raise

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> bool:
        """Delete an alert rule"""
        try:
            db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not db_rule:
                return False
                
            # Deactivate instead of deleting if there are associated alerts
            alert_count = db.query(Alert).filter(Alert.rule_id == rule_id).count()
            if alert_count > 0:
                db_rule.is_active = False
                db_rule.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Deactivated alert rule {rule_id} (has {alert_count} associated alerts)")
            else:
                db.delete(db_rule)
                db.commit()
                logger.info(f"Deleted alert rule {rule_id}")
                
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete alert rule {rule_id}: {str(e)}")
            raise

    @staticmethod
    def test_rule(db: Session, request: TestRuleRequest) -> TestRuleResponse:
        """Test an alert rule against sample data"""
        try:
            # Get the rule if rule_id is provided, otherwise use the test conditions
            if request.rule_id:
                rule = db.query(AlertRule).filter(AlertRule.id == request.rule_id).first()
                if not rule:
                    return TestRuleResponse(
                        success=False,
                        would_trigger=False,
                        error="Rule not found"
                    )
                conditions = rule.conditions
                alert_type = rule.alert_type
            else:
                conditions = request.conditions
                alert_type = request.alert_type
                
            # Validate conditions
            try:
                RuleService._validate_rule_conditions(alert_type, conditions)
            except ValueError as e:
                return TestRuleResponse(
                    success=False,
                    would_trigger=False,
                    error=f"Invalid conditions: {str(e)}"
                )
            
            # Test the conditions against sample data
            would_trigger = RuleService._evaluate_conditions(conditions, request.sample_data)
            
            # Generate explanation
            explanation = RuleService._generate_test_explanation(
                conditions, 
                request.sample_data, 
                would_trigger
            )
            
            return TestRuleResponse(
                success=True,
                would_trigger=would_trigger,
                explanation=explanation,
                matched_conditions=RuleService._get_matched_conditions(conditions, request.sample_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to test rule: {str(e)}")
            return TestRuleResponse(
                success=False,
                would_trigger=False,
                error=str(e)
            )

    @staticmethod
    def _validate_rule_conditions(alert_type: AlertType, conditions: Dict[str, Any]) -> None:
        """Validate rule conditions based on alert type"""
        
        if alert_type == AlertType.SENTIMENT_THRESHOLD:
            required_fields = ["sentiment_score", "threshold"]
            for field in required_fields:
                if field not in conditions:
                    raise ValueError(f"Missing required field for sentiment threshold: {field}")
            
            if not isinstance(conditions["threshold"], (int, float)):
                raise ValueError("Threshold must be a number")
            
            if not -1 <= conditions["threshold"] <= 1:
                raise ValueError("Sentiment threshold must be between -1 and 1")
                
        elif alert_type == AlertType.VOLUME_SPIKE:
            required_fields = ["volume_field", "threshold_multiplier"]
            for field in required_fields:
                if field not in conditions:
                    raise ValueError(f"Missing required field for volume spike: {field}")
            
            if not isinstance(conditions["threshold_multiplier"], (int, float)):
                raise ValueError("Threshold multiplier must be a number")
                
            if conditions["threshold_multiplier"] <= 1:
                raise ValueError("Threshold multiplier must be greater than 1")
                
        elif alert_type == AlertType.KEYWORD_MENTION:
            required_fields = ["keywords"]
            for field in required_fields:
                if field not in conditions:
                    raise ValueError(f"Missing required field for keyword mention: {field}")
            
            if not isinstance(conditions["keywords"], list):
                raise ValueError("Keywords must be a list")
                
            if len(conditions["keywords"]) == 0:
                raise ValueError("At least one keyword must be specified")
                
        elif alert_type == AlertType.TREND_CHANGE:
            required_fields = ["trend_field", "change_threshold"]
            for field in required_fields:
                if field not in conditions:
                    raise ValueError(f"Missing required field for trend change: {field}")
            
            if not isinstance(conditions["change_threshold"], (int, float)):
                raise ValueError("Change threshold must be a number")
                
        elif alert_type == AlertType.CUSTOM:
            # Custom rules should have at least one condition
            if not conditions:
                raise ValueError("Custom rules must have at least one condition")
        
        else:
            raise ValueError(f"Unknown alert type: {alert_type}")

    @staticmethod
    def _evaluate_conditions(conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate conditions against data"""
        try:
            for condition_key, condition_value in conditions.items():
                if condition_key not in data:
                    return False
                    
                data_value = data[condition_key]
                
                # Handle different condition types
                if isinstance(condition_value, dict):
                    # Complex conditions with operators
                    if "operator" in condition_value and "threshold" in condition_value:
                        operator = condition_value["operator"]
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
                        elif operator == "ne" and data_value == threshold:
                            return False
                    else:
                        # Nested conditions - recursively evaluate
                        if not RuleService._evaluate_conditions(condition_value, data):
                            return False
                            
                elif isinstance(condition_value, list):
                    # List conditions (e.g., keywords)
                    if condition_key == "keywords":
                        # Check if any keyword is mentioned in the data
                        text_fields = ["content", "title", "text", "message"]
                        found_keyword = False
                        
                        for text_field in text_fields:
                            if text_field in data and isinstance(data[text_field], str):
                                text_content = data[text_field].lower()
                                for keyword in condition_value:
                                    if keyword.lower() in text_content:
                                        found_keyword = True
                                        break
                                if found_keyword:
                                    break
                        
                        if not found_keyword:
                            return False
                    else:
                        # Direct list comparison
                        if data_value not in condition_value:
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
    def _generate_test_explanation(
        conditions: Dict[str, Any], 
        data: Dict[str, Any], 
        would_trigger: bool
    ) -> str:
        """Generate human-readable explanation of test results"""
        explanations = []
        
        for condition_key, condition_value in conditions.items():
            data_value = data.get(condition_key, "N/A")
            
            if isinstance(condition_value, dict) and "operator" in condition_value:
                operator = condition_value["operator"]
                threshold = condition_value["threshold"]
                
                op_text = {
                    "gte": "greater than or equal to",
                    "lte": "less than or equal to", 
                    "gt": "greater than",
                    "lt": "less than",
                    "eq": "equal to",
                    "ne": "not equal to"
                }.get(operator, operator)
                
                explanations.append(
                    f"{condition_key}: {data_value} should be {op_text} {threshold}"
                )
                
            elif isinstance(condition_value, list):
                if condition_key == "keywords":
                    explanations.append(
                        f"Keywords {condition_value} should be found in text content"
                    )
                else:
                    explanations.append(
                        f"{condition_key}: {data_value} should be in {condition_value}"
                    )
            else:
                explanations.append(
                    f"{condition_key}: {data_value} should equal {condition_value}"
                )
        
        result_text = "WOULD TRIGGER" if would_trigger else "WOULD NOT TRIGGER"
        return f"Rule {result_text}. Conditions: " + "; ".join(explanations)

    @staticmethod
    def _get_matched_conditions(conditions: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
        """Get list of conditions that matched"""
        matched = []
        
        for condition_key, condition_value in conditions.items():
            if condition_key not in data:
                continue
                
            data_value = data[condition_key]
            condition_matched = False
            
            if isinstance(condition_value, dict) and "operator" in condition_value:
                operator = condition_value["operator"]
                threshold = condition_value["threshold"]
                
                if operator == "gte" and data_value >= threshold:
                    condition_matched = True
                elif operator == "lte" and data_value <= threshold:
                    condition_matched = True
                elif operator == "eq" and data_value == threshold:
                    condition_matched = True
                elif operator == "gt" and data_value > threshold:
                    condition_matched = True
                elif operator == "lt" and data_value < threshold:
                    condition_matched = True
                elif operator == "ne" and data_value != threshold:
                    condition_matched = True
                    
            elif isinstance(condition_value, list):
                if condition_key == "keywords":
                    # Check if any keyword is found
                    text_fields = ["content", "title", "text", "message"]
                    for text_field in text_fields:
                        if text_field in data and isinstance(data[text_field], str):
                            text_content = data[text_field].lower()
                            for keyword in condition_value:
                                if keyword.lower() in text_content:
                                    condition_matched = True
                                    break
                            if condition_matched:
                                break
                else:
                    condition_matched = data_value in condition_value
            else:
                condition_matched = data_value == condition_value
            
            if condition_matched:
                matched.append(condition_key)
        
        return matched

    @staticmethod
    def get_rule_templates() -> Dict[str, Any]:
        """Get rule templates for different alert types"""
        return {
            AlertType.SENTIMENT_THRESHOLD: {
                "name": "Sentiment Threshold Alert",
                "description": "Trigger when sentiment score crosses a threshold",
                "conditions": {
                    "sentiment_score": {
                        "operator": "lte",
                        "threshold": -0.5
                    }
                },
                "notification_template": "Alert: Sentiment score {sentiment_score} is below threshold {conditions[sentiment_score][threshold]}"
            },
            AlertType.VOLUME_SPIKE: {
                "name": "Volume Spike Alert", 
                "description": "Trigger when data volume spikes above normal",
                "conditions": {
                    "volume_field": "article_count",
                    "threshold_multiplier": 2.0,
                    "baseline_period_hours": 24
                },
                "notification_template": "Alert: Volume spike detected - {volume_field} is {threshold_multiplier}x above baseline"
            },
            AlertType.KEYWORD_MENTION: {
                "name": "Keyword Mention Alert",
                "description": "Trigger when specific keywords are mentioned",
                "conditions": {
                    "keywords": ["pension crisis", "retirement fund collapse", "pension deficit"],
                    "case_sensitive": False
                },
                "notification_template": "Alert: Keywords detected in content: {matched_keywords}"
            },
            AlertType.TREND_CHANGE: {
                "name": "Trend Change Alert",
                "description": "Trigger when a trend changes significantly", 
                "conditions": {
                    "trend_field": "sentiment_trend",
                    "change_threshold": 0.3,
                    "comparison_period_hours": 24
                },
                "notification_template": "Alert: Significant trend change detected in {trend_field}"
            },
            AlertType.CUSTOM: {
                "name": "Custom Alert Rule",
                "description": "Define custom conditions for alerts",
                "conditions": {
                    "custom_field": {
                        "operator": "gte", 
                        "threshold": 1
                    }
                },
                "notification_template": "Custom alert triggered: {custom_field} = {custom_field_value}"
            }
        }

    @staticmethod
    def get_rule_documentation() -> Dict[str, Any]:
        """Get documentation for rule configuration"""
        return {
            "alert_types": {
                AlertType.SENTIMENT_THRESHOLD: {
                    "description": "Triggers when sentiment analysis scores cross defined thresholds",
                    "required_conditions": ["sentiment_score", "threshold"],
                    "optional_conditions": ["operator"],
                    "supported_operators": ["gte", "lte", "gt", "lt", "eq"],
                    "example_data": {
                        "sentiment_score": -0.7,
                        "content": "Negative news about pensions",
                        "source": "news_article"
                    }
                },
                AlertType.VOLUME_SPIKE: {
                    "description": "Triggers when data volume exceeds normal patterns",
                    "required_conditions": ["volume_field", "threshold_multiplier"],
                    "optional_conditions": ["baseline_period_hours"],
                    "example_data": {
                        "article_count": 150,
                        "normal_count": 50,
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                },
                AlertType.KEYWORD_MENTION: {
                    "description": "Triggers when specific keywords appear in content",
                    "required_conditions": ["keywords"],
                    "optional_conditions": ["case_sensitive"],
                    "example_data": {
                        "content": "The pension crisis is affecting millions",
                        "title": "Breaking News on Retirement",
                        "keywords_found": ["pension crisis"]
                    }
                },
                AlertType.TREND_CHANGE: {
                    "description": "Triggers when trends change significantly over time",
                    "required_conditions": ["trend_field", "change_threshold"],
                    "optional_conditions": ["comparison_period_hours"],
                    "example_data": {
                        "sentiment_trend": 0.8,
                        "previous_trend": 0.1,
                        "change_magnitude": 0.7
                    }
                },
                AlertType.CUSTOM: {
                    "description": "Allows custom condition logic for specialized use cases",
                    "required_conditions": ["At least one condition"],
                    "optional_conditions": ["Any field with operators"],
                    "supported_operators": ["gte", "lte", "gt", "lt", "eq", "ne"],
                    "example_data": {
                        "custom_metric": 42,
                        "status": "critical",
                        "priority": "high"
                    }
                }
            },
            "operators": {
                "gte": "Greater than or equal to",
                "lte": "Less than or equal to", 
                "gt": "Greater than",
                "lt": "Less than",
                "eq": "Equal to",
                "ne": "Not equal to"
            },
            "notification_template_variables": [
                "rule_name", "alert_type", "severity", "created_at",
                "Any field from the input data", 
                "Any field from rule conditions (using conditions[field_name] syntax)"
            ]
        }

    @staticmethod
    def validate_rule_config(alert_type: AlertType, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and return feedback on rule configuration"""
        try:
            RuleService._validate_rule_conditions(alert_type, conditions)
            return {
                "valid": True,
                "message": "Rule configuration is valid",
                "suggestions": RuleService._get_rule_suggestions(alert_type, conditions)
            }
        except ValueError as e:
            return {
                "valid": False,
                "message": str(e),
                "suggestions": RuleService._get_fix_suggestions(alert_type, conditions, str(e))
            }

    @staticmethod 
    def _get_rule_suggestions(alert_type: AlertType, conditions: Dict[str, Any]) -> List[str]:
        """Get suggestions for improving rule configuration"""
        suggestions = []
        
        if alert_type == AlertType.SENTIMENT_THRESHOLD:
            threshold = conditions.get("threshold", 0)
            if threshold > 0.8:
                suggestions.append("High positive threshold - consider if you want to alert on very positive sentiment")
            elif threshold < -0.8:
                suggestions.append("Very negative threshold - may generate frequent alerts")
                
        elif alert_type == AlertType.VOLUME_SPIKE:
            multiplier = conditions.get("threshold_multiplier", 1)
            if multiplier < 1.5:
                suggestions.append("Low threshold multiplier may cause frequent false positives")
            elif multiplier > 5:
                suggestions.append("High threshold multiplier may miss significant spikes")
                
        elif alert_type == AlertType.KEYWORD_MENTION:
            keywords = conditions.get("keywords", [])
            if len(keywords) > 20:
                suggestions.append("Large number of keywords may impact performance")
            if any(len(kw) < 3 for kw in keywords):
                suggestions.append("Very short keywords may cause false positives")
        
        return suggestions

    @staticmethod
    def _get_fix_suggestions(
        alert_type: AlertType, 
        conditions: Dict[str, Any], 
        error: str
    ) -> List[str]:
        """Get suggestions for fixing rule configuration errors"""
        suggestions = []
        
        if "Missing required field" in error:
            templates = RuleService.get_rule_templates()
            if alert_type in templates:
                template_conditions = templates[alert_type]["conditions"]
                suggestions.append(f"Required fields: {list(template_conditions.keys())}")
                suggestions.append(f"Example: {template_conditions}")
        
        elif "must be a number" in error:
            suggestions.append("Ensure numeric fields contain valid numbers (int or float)")
            
        elif "must be a list" in error:
            suggestions.append("Ensure list fields are formatted as arrays: [\"item1\", \"item2\"]")
            
        elif "Threshold" in error and "between" in error:
            suggestions.append("Sentiment thresholds should be between -1.0 (very negative) and 1.0 (very positive)")
            
        return suggestions