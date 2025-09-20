from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db, Notification, AlertSubscription
from app.schemas import (
    Notification as NotificationSchema,
    NotificationCreate,
    NotificationUpdate,
    AlertSubscription as AlertSubscriptionSchema,
    AlertSubscriptionCreate,
    AlertSubscriptionUpdate,
    NotificationStats
)
from app.services.notification_service import NotificationService

router = APIRouter()

# Notification endpoints
@router.get("/", response_model=List[NotificationSchema])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    alert_id: Optional[int] = Query(None),
    recipient: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all notifications with optional filtering"""
    notification_service = NotificationService(db)
    return notification_service.get_notifications(
        skip=skip,
        limit=limit,
        status=status,
        channel=channel,
        alert_id=alert_id,
        recipient=recipient
    )

@router.get("/{notification_id}", response_model=NotificationSchema)
async def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get a specific notification by ID"""
    notification_service = NotificationService(db)
    notification = notification_service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    return notification

@router.post("/", response_model=NotificationSchema)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification"""
    notification_service = NotificationService(db)
    
    try:
        notification = notification_service.create_notification(notification_data)
        return notification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.patch("/{notification_id}", response_model=NotificationSchema)
async def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db)
):
    """Update a notification"""
    notification_service = NotificationService(db)
    
    notification = notification_service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    try:
        updated_notification = notification_service.update_notification(notification_id, notification_update)
        return updated_notification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update notification: {str(e)}"
        )

@router.post("/{notification_id}/retry")
async def retry_notification(notification_id: int, db: Session = Depends(get_db)):
    """Retry a failed notification"""
    notification_service = NotificationService(db)
    
    notification = notification_service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    if notification.status not in ["failed", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry notification with status '{notification.status}'"
        )
    
    try:
        result = await notification_service.retry_notification(notification_id)
        return {"message": "Notification retry initiated", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry notification: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification"""
    notification_service = NotificationService(db)
    
    notification = notification_service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    try:
        notification_service.delete_notification(notification_id)
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

# Subscription endpoints
@router.get("/subscriptions/", response_model=List[AlertSubscriptionSchema])
async def get_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all alert subscriptions with optional filtering"""
    notification_service = NotificationService(db)
    return notification_service.get_subscriptions(
        skip=skip,
        limit=limit,
        user_id=user_id,
        is_active=is_active
    )

@router.get("/subscriptions/{subscription_id}", response_model=AlertSubscriptionSchema)
async def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Get a specific subscription by ID"""
    notification_service = NotificationService(db)
    subscription = notification_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    return subscription

@router.post("/subscriptions/", response_model=AlertSubscriptionSchema)
async def create_subscription(
    subscription_data: AlertSubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert subscription"""
    notification_service = NotificationService(db)
    
    try:
        # Check if user already has a subscription
        existing = notification_service.get_user_subscription(subscription_data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {subscription_data.user_id} already has a subscription"
            )
        
        subscription = notification_service.create_subscription(subscription_data)
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.put("/subscriptions/{subscription_id}", response_model=AlertSubscriptionSchema)
async def update_subscription(
    subscription_id: int,
    subscription_update: AlertSubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert subscription"""
    notification_service = NotificationService(db)
    
    subscription = notification_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    
    try:
        updated_subscription = notification_service.update_subscription(subscription_id, subscription_update)
        return updated_subscription
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update subscription: {str(e)}"
        )

@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Delete an alert subscription"""
    notification_service = NotificationService(db)
    
    subscription = notification_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    
    try:
        notification_service.delete_subscription(subscription_id)
        return {"message": "Subscription deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subscription: {str(e)}"
        )

@router.get("/subscriptions/user/{user_id}", response_model=AlertSubscriptionSchema)
async def get_user_subscription(user_id: str, db: Session = Depends(get_db)):
    """Get subscription for a specific user"""
    notification_service = NotificationService(db)
    subscription = notification_service.get_user_subscription(user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subscription found for user {user_id}"
        )
    return subscription

# Stats and monitoring endpoints
@router.get("/stats/overview", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get notification statistics overview"""
    notification_service = NotificationService(db)
    return notification_service.get_notification_stats(days)

@router.get("/stats/delivery-rates")
async def get_delivery_rates(
    days: int = Query(7, ge=1, le=365),
    channel: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get delivery rates by channel and time period"""
    notification_service = NotificationService(db)
    return notification_service.get_delivery_rates(days, channel)

@router.get("/channels/status")
async def get_channel_status(db: Session = Depends(get_db)):
    """Get status of all notification channels"""
    notification_service = NotificationService(db)
    return notification_service.get_channel_status()

# Webhook endpoints for external services
@router.post("/webhooks/email-delivery")
async def email_delivery_webhook(
    notification_id: int,
    status: str,
    external_id: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Webhook endpoint for email delivery status updates"""
    notification_service = NotificationService(db)
    
    try:
        notification_service.update_delivery_status(
            notification_id=notification_id,
            status=status,
            external_id=external_id,
            error_message=error_message
        )
        return {"message": "Delivery status updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update delivery status: {str(e)}"
        )

@router.post("/webhooks/slack-delivery")
async def slack_delivery_webhook(
    notification_id: int,
    status: str,
    external_id: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Webhook endpoint for Slack delivery status updates"""
    notification_service = NotificationService(db)
    
    try:
        notification_service.update_delivery_status(
            notification_id=notification_id,
            status=status,
            external_id=external_id,
            error_message=error_message
        )
        return {"message": "Delivery status updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update delivery status: {str(e)}"
        )

# Test endpoints
@router.post("/test-email")
async def test_email_notification(
    recipient: str,
    subject: str = "Test Notification",
    content: str = "This is a test notification from the Alert Service",
    db: Session = Depends(get_db)
):
    """Send a test email notification"""
    notification_service = NotificationService(db)
    
    try:
        result = await notification_service.send_test_notification(
            channel="email",
            recipient=recipient,
            subject=subject,
            content=content
        )
        return {"message": "Test notification sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )

@router.post("/test-slack")
async def test_slack_notification(
    recipient: str,  # Slack channel or user ID
    content: str = "This is a test notification from the Alert Service",
    db: Session = Depends(get_db)
):
    """Send a test Slack notification"""
    notification_service = NotificationService(db)
    
    try:
        result = await notification_service.send_test_notification(
            channel="slack",
            recipient=recipient,
            content=content
        )
        return {"message": "Test notification sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )