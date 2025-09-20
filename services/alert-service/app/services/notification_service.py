from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import smtplib
import json
import requests
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from app.db import Notification, AlertSubscription, Alert, get_db
from app.schemas import (
    NotificationCreate, NotificationUpdate, AlertSubscriptionCreate,
    AlertSubscriptionUpdate, NotificationStats, NotificationChannel
)
from app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def create_notification(db: Session, notification_data: NotificationCreate) -> Notification:
        """Create a new notification"""
        try:
            db_notification = Notification(**notification_data.dict())
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            logger.info(f"Created notification {db_notification.id}")
            return db_notification
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create notification: {str(e)}")
            raise

    @staticmethod
    def get_notification(db: Session, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return db.query(Notification).filter(Notification.id == notification_id).first()

    @staticmethod
    def get_notifications(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel: Optional[NotificationChannel] = None,
        status: Optional[str] = None,
        alert_id: Optional[int] = None
    ) -> List[Notification]:
        """Get notifications with filtering"""
        query = db.query(Notification)
        
        if channel:
            query = query.filter(Notification.channel == channel)
        if status:
            query = query.filter(Notification.status == status)
        if alert_id:
            query = query.filter(Notification.alert_id == alert_id)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def send_notification(db: Session, alert: Alert, channels: List[str]) -> List[Notification]:
        """Send notifications for an alert across multiple channels"""
        notifications = []
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    notification = NotificationService._send_email_notification(db, alert)
                elif channel == NotificationChannel.SLACK:
                    notification = NotificationService._send_slack_notification(db, alert)
                elif channel == NotificationChannel.SMS:
                    notification = NotificationService._send_sms_notification(db, alert)
                elif channel == NotificationChannel.WEBHOOK:
                    notification = NotificationService._send_webhook_notification(db, alert)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
                    continue
                    
                if notification:
                    notifications.append(notification)
                    
            except Exception as e:
                logger.error(f"Failed to send {channel} notification for alert {alert.id}: {str(e)}")
                # Create failed notification record
                notification_data = NotificationCreate(
                    alert_id=alert.id,
                    channel=channel,
                    recipient="unknown",
                    subject=f"Alert: {alert.title}",
                    message=alert.message,
                    status="failed",
                    error_message=str(e)
                )
                notification = NotificationService.create_notification(db, notification_data)
                notifications.append(notification)
        
        return notifications

    @staticmethod
    def _send_email_notification(db: Session, alert: Alert) -> Optional[Notification]:
        """Send email notification"""
        try:
            # Get email recipients
            recipients = NotificationService._get_email_recipients(db, alert)
            if not recipients:
                logger.info(f"No email recipients found for alert {alert.id}")
                return None

            # Prepare email content
            subject = f"[{alert.severity.upper()}] {alert.title}"
            html_content = NotificationService._generate_email_html(alert)
            text_content = NotificationService._generate_email_text(alert)

            # Send email
            sent_count = 0
            for recipient in recipients:
                try:
                    msg = MimeMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = settings.smtp_from_email
                    msg['To'] = recipient

                    # Attach both text and HTML versions
                    msg.attach(MimeText(text_content, 'plain'))
                    msg.attach(MimeText(html_content, 'html'))

                    # Send via SMTP
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                        if settings.smtp_use_tls:
                            server.starttls()
                        if settings.smtp_username and settings.smtp_password:
                            server.login(settings.smtp_username, settings.smtp_password)
                        server.send_message(msg)
                    
                    sent_count += 1
                    logger.info(f"Email sent to {recipient} for alert {alert.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient}: {str(e)}")

            # Create notification record
            notification_data = NotificationCreate(
                alert_id=alert.id,
                channel=NotificationChannel.EMAIL,
                recipient=", ".join(recipients),
                subject=subject,
                message=text_content,
                status="sent" if sent_count > 0 else "failed",
                metadata={"sent_count": sent_count, "total_recipients": len(recipients)}
            )
            
            return NotificationService.create_notification(db, notification_data)

        except Exception as e:
            logger.error(f"Email notification failed for alert {alert.id}: {str(e)}")
            raise

    @staticmethod
    def _send_slack_notification(db: Session, alert: Alert) -> Optional[Notification]:
        """Send Slack notification"""
        try:
            if not settings.slack_webhook_url:
                logger.warning("Slack webhook URL not configured")
                return None

            # Prepare Slack message
            color_map = {
                "low": "#36a64f",      # Green
                "medium": "#ff9500",   # Orange
                "high": "#ff0000",     # Red
                "critical": "#8B0000"  # Dark Red
            }
            
            color = color_map.get(alert.severity.value, "#36a64f")
            
            slack_payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Alert: {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Type",
                                "value": alert.alert_type.value.replace("_", " ").title(),
                                "short": True
                            },
                            {
                                "title": "Created",
                                "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True
                            }
                        ],
                        "footer": "Pension Sentiment Alert System",
                        "ts": int(alert.created_at.timestamp())
                    }
                ]
            }

            # Send to Slack
            response = requests.post(
                settings.slack_webhook_url,
                json=slack_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                status = "sent"
                error_message = None
                logger.info(f"Slack notification sent for alert {alert.id}")
            else:
                status = "failed"
                error_message = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Slack notification failed: {error_message}")

            # Create notification record
            notification_data = NotificationCreate(
                alert_id=alert.id,
                channel=NotificationChannel.SLACK,
                recipient=settings.slack_channel or "default",
                subject=f"Alert: {alert.title}",
                message=alert.message,
                status=status,
                error_message=error_message,
                metadata={"webhook_url": settings.slack_webhook_url}
            )
            
            return NotificationService.create_notification(db, notification_data)

        except Exception as e:
            logger.error(f"Slack notification failed for alert {alert.id}: {str(e)}")
            raise

    @staticmethod
    def _send_sms_notification(db: Session, alert: Alert) -> Optional[Notification]:
        """Send SMS notification"""
        try:
            # Get SMS recipients
            recipients = NotificationService._get_sms_recipients(db, alert)
            if not recipients:
                logger.info(f"No SMS recipients found for alert {alert.id}")
                return None

            # Prepare SMS message (keep it short)
            message = f"[{alert.severity.upper()}] {alert.title}: {alert.message[:100]}..."
            
            # This is a placeholder for SMS service integration
            # You would integrate with services like Twilio, AWS SNS, etc.
            logger.info(f"SMS notification would be sent to {len(recipients)} recipients")
            
            # Create notification record
            notification_data = NotificationCreate(
                alert_id=alert.id,
                channel=NotificationChannel.SMS,
                recipient=", ".join(recipients),
                subject=f"Alert: {alert.title}",
                message=message,
                status="pending",  # Would be "sent" after actual SMS service integration
                metadata={"recipient_count": len(recipients)}
            )
            
            return NotificationService.create_notification(db, notification_data)

        except Exception as e:
            logger.error(f"SMS notification failed for alert {alert.id}: {str(e)}")
            raise

    @staticmethod
    def _send_webhook_notification(db: Session, alert: Alert) -> Optional[Notification]:
        """Send webhook notification"""
        try:
            # Get webhook URLs from subscriptions
            webhook_urls = NotificationService._get_webhook_urls(db, alert)
            if not webhook_urls:
                logger.info(f"No webhook URLs found for alert {alert.id}")
                return None

            # Prepare webhook payload
            webhook_payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "alert_type": alert.alert_type.value,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "data": alert.data
            }

            sent_count = 0
            for url in webhook_urls:
                try:
                    response = requests.post(
                        url,
                        json=webhook_payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        sent_count += 1
                        logger.info(f"Webhook sent to {url} for alert {alert.id}")
                    else:
                        logger.error(f"Webhook failed for {url}: HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Webhook failed for {url}: {str(e)}")

            # Create notification record
            notification_data = NotificationCreate(
                alert_id=alert.id,
                channel=NotificationChannel.WEBHOOK,
                recipient=", ".join(webhook_urls),
                subject=f"Alert: {alert.title}",
                message=json.dumps(webhook_payload),
                status="sent" if sent_count > 0 else "failed",
                metadata={"sent_count": sent_count, "total_webhooks": len(webhook_urls)}
            )
            
            return NotificationService.create_notification(db, notification_data)

        except Exception as e:
            logger.error(f"Webhook notification failed for alert {alert.id}: {str(e)}")
            raise

    @staticmethod
    def _get_email_recipients(db: Session, alert: Alert) -> List[str]:
        """Get email recipients for an alert"""
        # Get email subscriptions
        subscriptions = db.query(AlertSubscription).filter(
            AlertSubscription.channel == NotificationChannel.EMAIL,
            AlertSubscription.is_active == True
        ).all()
        
        # Filter based on alert criteria
        recipients = []
        for sub in subscriptions:
            if NotificationService._matches_subscription(alert, sub):
                recipients.append(sub.recipient)
        
        return recipients

    @staticmethod
    def _get_sms_recipients(db: Session, alert: Alert) -> List[str]:
        """Get SMS recipients for an alert"""
        subscriptions = db.query(AlertSubscription).filter(
            AlertSubscription.channel == NotificationChannel.SMS,
            AlertSubscription.is_active == True
        ).all()
        
        recipients = []
        for sub in subscriptions:
            if NotificationService._matches_subscription(alert, sub):
                recipients.append(sub.recipient)
        
        return recipients

    @staticmethod
    def _get_webhook_urls(db: Session, alert: Alert) -> List[str]:
        """Get webhook URLs for an alert"""
        subscriptions = db.query(AlertSubscription).filter(
            AlertSubscription.channel == NotificationChannel.WEBHOOK,
            AlertSubscription.is_active == True
        ).all()
        
        urls = []
        for sub in subscriptions:
            if NotificationService._matches_subscription(alert, sub):
                urls.append(sub.recipient)
        
        return urls

    @staticmethod
    def _matches_subscription(alert: Alert, subscription: AlertSubscription) -> bool:
        """Check if alert matches subscription criteria"""
        # Check severity filter
        if subscription.severity_filter and alert.severity.value not in subscription.severity_filter:
            return False
        
        # Check alert type filter
        if subscription.alert_type_filter and alert.alert_type.value not in subscription.alert_type_filter:
            return False
        
        # Check quiet hours
        if subscription.quiet_hours_start and subscription.quiet_hours_end:
            current_time = datetime.utcnow().time()
            start_time = subscription.quiet_hours_start
            end_time = subscription.quiet_hours_end
            
            if start_time <= end_time:
                # Same day
                if start_time <= current_time <= end_time:
                    return False
            else:
                # Spans midnight
                if current_time >= start_time or current_time <= end_time:
                    return False
        
        return True

    @staticmethod
    def _generate_email_html(alert: Alert) -> str:
        """Generate HTML email content"""
        return f"""
        <html>
        <body>
            <h2 style="color: {'#ff0000' if alert.severity.value in ['high', 'critical'] else '#ff9500' if alert.severity.value == 'medium' else '#36a64f'};">
                Alert: {alert.title}
            </h2>
            <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
            <p><strong>Type:</strong> {alert.alert_type.value.replace('_', ' ').title()}</p>
            <p><strong>Created:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <hr>
            <p>{alert.message}</p>
            {f'<p><strong>Additional Data:</strong><br><pre>{json.dumps(alert.data, indent=2)}</pre></p>' if alert.data else ''}
            <hr>
            <p><small>This alert was generated by the Pension Sentiment Analysis System.</small></p>
        </body>
        </html>
        """

    @staticmethod
    def _generate_email_text(alert: Alert) -> str:
        """Generate plain text email content"""
        return f"""
Alert: {alert.title}

Severity: {alert.severity.value.upper()}
Type: {alert.alert_type.value.replace('_', ' ').title()}
Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

{alert.message}

{f'Additional Data: {json.dumps(alert.data, indent=2)}' if alert.data else ''}

---
This alert was generated by the Pension Sentiment Analysis System.
        """.strip()

    @staticmethod
    def create_subscription(db: Session, subscription_data: AlertSubscriptionCreate) -> AlertSubscription:
        """Create a new alert subscription"""
        try:
            db_subscription = AlertSubscription(**subscription_data.dict())
            db.add(db_subscription)
            db.commit()
            db.refresh(db_subscription)
            logger.info(f"Created subscription {db_subscription.id}")
            return db_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create subscription: {str(e)}")
            raise

    @staticmethod
    def get_subscription(db: Session, subscription_id: int) -> Optional[AlertSubscription]:
        """Get subscription by ID"""
        return db.query(AlertSubscription).filter(AlertSubscription.id == subscription_id).first()

    @staticmethod
    def get_subscriptions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel: Optional[NotificationChannel] = None,
        is_active: Optional[bool] = None
    ) -> List[AlertSubscription]:
        """Get subscriptions with filtering"""
        query = db.query(AlertSubscription)
        
        if channel:
            query = query.filter(AlertSubscription.channel == channel)
        if is_active is not None:
            query = query.filter(AlertSubscription.is_active == is_active)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_subscription(
        db: Session, 
        subscription_id: int, 
        subscription_data: AlertSubscriptionUpdate
    ) -> Optional[AlertSubscription]:
        """Update a subscription"""
        try:
            db_subscription = db.query(AlertSubscription).filter(
                AlertSubscription.id == subscription_id
            ).first()
            if not db_subscription:
                return None
                
            update_data = subscription_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_subscription, field, value)
                
            db_subscription.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_subscription)
            logger.info(f"Updated subscription {subscription_id}")
            return db_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def delete_subscription(db: Session, subscription_id: int) -> bool:
        """Delete a subscription"""
        try:
            db_subscription = db.query(AlertSubscription).filter(
                AlertSubscription.id == subscription_id
            ).first()
            if not db_subscription:
                return False
                
            db.delete(db_subscription)
            db.commit()
            logger.info(f"Deleted subscription {subscription_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def get_notification_stats(db: Session) -> NotificationStats:
        """Get notification statistics"""
        total_notifications = db.query(Notification).count()
        sent_notifications = db.query(Notification).filter(Notification.status == "sent").count()
        failed_notifications = db.query(Notification).filter(Notification.status == "failed").count()
        pending_notifications = db.query(Notification).filter(Notification.status == "pending").count()
        
        # Channel breakdown
        channel_stats = {}
        for channel in NotificationChannel:
            count = db.query(Notification).filter(Notification.channel == channel).count()
            channel_stats[channel.value] = count
        
        # Recent notifications (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_notifications = db.query(Notification).filter(Notification.created_at >= last_24h).count()
        
        return NotificationStats(
            total_notifications=total_notifications,
            sent_notifications=sent_notifications,
            failed_notifications=failed_notifications,
            pending_notifications=pending_notifications,
            recent_notifications=recent_notifications,
            channel_breakdown=channel_stats
        )

    @staticmethod
    def test_notification_channel(db: Session, channel: NotificationChannel, recipient: str) -> Dict[str, Any]:
        """Test a notification channel"""
        try:
            # Create a test alert
            test_alert = Alert(
                id=0,  # Test ID
                title="Test Notification",
                message="This is a test notification from the Pension Sentiment Alert System.",
                severity="low",
                alert_type="custom",
                status="active",
                created_at=datetime.utcnow()
            )
            
            # Send test notification
            if channel == NotificationChannel.EMAIL:
                # Test email
                result = NotificationService._send_test_email(recipient, test_alert)
            elif channel == NotificationChannel.SLACK:
                # Test Slack
                result = NotificationService._send_test_slack(test_alert)
            elif channel == NotificationChannel.SMS:
                # Test SMS
                result = NotificationService._send_test_sms(recipient, test_alert)
            elif channel == NotificationChannel.WEBHOOK:
                # Test webhook
                result = NotificationService._send_test_webhook(recipient, test_alert)
            else:
                return {"success": False, "error": f"Unknown channel: {channel}"}
            
            return result
            
        except Exception as e:
            logger.error(f"Test notification failed for {channel}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _send_test_email(recipient: str, alert: Alert) -> Dict[str, Any]:
        """Send test email"""
        try:
            subject = "[TEST] Pension Sentiment Alert System"
            message = "This is a test email to verify email notifications are working correctly."
            
            msg = MimeText(message)
            msg['Subject'] = subject
            msg['From'] = settings.smtp_from_email
            msg['To'] = recipient
            
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Test email sent to {recipient}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _send_test_slack(alert: Alert) -> Dict[str, Any]:
        """Send test Slack message"""
        try:
            if not settings.slack_webhook_url:
                return {"success": False, "error": "Slack webhook URL not configured"}
            
            payload = {
                "text": "Test notification from Pension Sentiment Alert System",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "title": "Test Alert",
                        "text": "This is a test message to verify Slack notifications are working correctly.",
                        "footer": "Pension Sentiment Alert System"
                    }
                ]
            }
            
            response = requests.post(
                settings.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Test Slack message sent successfully"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _send_test_sms(recipient: str, alert: Alert) -> Dict[str, Any]:
        """Send test SMS"""
        # Placeholder for SMS testing
        return {
            "success": True, 
            "message": f"Test SMS would be sent to {recipient} (SMS service not implemented)"
        }

    @staticmethod
    def _send_test_webhook(webhook_url: str, alert: Alert) -> Dict[str, Any]:
        """Send test webhook"""
        try:
            payload = {
                "test": True,
                "message": "Test webhook from Pension Sentiment Alert System",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                return {"success": True, "message": f"Test webhook sent to {webhook_url}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}