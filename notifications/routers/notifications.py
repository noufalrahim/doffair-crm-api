"""
Notification API endpoints
Handles asynchronous notification requests across multiple channels
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from odmantic import AIOEngine
from typing import List, Optional
import logging

from notifications.schemas.notification_schema import (
    NotificationRequest,
    NotificationResponse,
    NotificationStatusResponse,
    InAppNotificationResponse,
    NotificationListResponse
)
from notifications.models.notification import NotificationLog, InAppNotification
from notifications.enums import NotificationStatus, NotificationChannel
from notifications.queue import notification_queue
from core.database import get_engine
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/send", response_model=dict, status_code=202)
async def send_notification(
    payload: NotificationRequest,
    engine: AIOEngine = Depends(get_engine)
):
    """
    Send notification across multiple channels asynchronously
    
    **Returns immediately** after queuing - does not wait for actual delivery
    
    **Supported Channels:**
    - `email`: Email notification
    - `sms`: SMS notification
    - `whatsapp`: WhatsApp message
    - `in_app`: In-app notification
    
    **Flow:**
    1. Validates request payload
    2. Creates notification record in database
    3. Pushes to Redis queue for background processing
    4. Returns immediately with notification ID
    5. Workers process in background
    
    **Example:**
    ```json
    {
        "channels": ["email", "sms", "in_app"],
        "recipient": {
            "user_id": "123",
            "email": "user@example.com",
            "phone": "+919876543210"
        },
        "template_id": "BOOKING_CONFIRMED",
        "data": {
            "booking_id": "BK123",
            "service_name": "Dog Grooming"
        }
    }
    ```
    """
    try:
        # Validate channel-specific recipient info
        channels_str = [ch.value for ch in payload.channels]
        
        if NotificationChannel.EMAIL.value in channels_str and not payload.recipient.email:
            raise HTTPException(status_code=400, detail="Email address required for email channel")
        
        if NotificationChannel.SMS.value in channels_str and not payload.recipient.phone:
            raise HTTPException(status_code=400, detail="Phone number required for SMS channel")
        
        if NotificationChannel.WHATSAPP.value in channels_str and not payload.recipient.whatsapp:
            raise HTTPException(status_code=400, detail="WhatsApp number required for WhatsApp channel")
        
        # Create notification log record
        notification_log = NotificationLog(
            user_id=payload.recipient.user_id,
            recipient_email=payload.recipient.email,
            recipient_phone=payload.recipient.phone,
            recipient_whatsapp=payload.recipient.whatsapp,
            channels=channels_str,
            template_id=payload.template_id,
            subject=payload.subject,
            message=payload.message,
            data=payload.data,
            event_type=payload.event_type,
            priority=payload.priority,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            scheduled_at=payload.scheduled_at,
            status=NotificationStatus.PENDING,
            channel_status={ch: NotificationStatus.PENDING.value for ch in channels_str}
        )
        
        # Save to database
        saved_notification = await engine.save(notification_log)
        notification_id = str(saved_notification.id)
        
        logger.info(f"📝 Created notification {notification_id} for user {payload.recipient.user_id}")
        
        # Enqueue for background processing (non-blocking)
        from bson import ObjectId
        queued_time = None
        
        try:
            job_id = notification_queue.enqueue_notification(
                notification_id=notification_id,
                job_timeout='5m'
            )
            
            # Update status to queued using MongoDB directly to avoid datetime validation issues
            queued_time = datetime.utcnow()
            await engine.get_collection(NotificationLog).update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {
                    "status": NotificationStatus.QUEUED.value,
                    "queued_at": queued_time
                }}
            )
            
            logger.info(f"✅ Notification {notification_id} queued successfully. Job ID: {job_id}")
            
        except Exception as queue_error:
            logger.error(f"❌ Failed to queue notification {notification_id}: {str(queue_error)}")
            
            # Update status to failed using MongoDB directly
            await engine.get_collection(NotificationLog).update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {
                    "status": NotificationStatus.FAILED.value,
                    "error_message": f"Failed to queue: {str(queue_error)}"
                }}
            )
            
            raise HTTPException(
                status_code=500,
                detail="Failed to queue notification for processing"
            )
        
        # Return immediately (async processing will happen in background)
        response = success_response(
            data=NotificationResponse(
                notification_id=notification_id,
                status=NotificationStatus.QUEUED.value,
                message="Notification queued for processing",
                queued_at=queued_time,
                channels=channels_str
            ).dict(),
            message="Notification request accepted and queued for processing"
        )
        return response.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing notification request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process notification: {str(e)}")


@router.get("/status/{notification_id}", response_model=dict)
async def get_notification_status(
    notification_id: str,
    engine: AIOEngine = Depends(get_engine)
):
    """
    Check the delivery status of a notification
    
    Returns the current status and per-channel delivery status
    """
    try:
        from bson import ObjectId
        
        # Fetch directly from MongoDB to avoid datetime validation issues
        notification_doc = await engine.get_collection(NotificationLog).find_one(
            {"_id": ObjectId(notification_id)}
        )
        
        if not notification_doc:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        response = success_response(
            data=NotificationStatusResponse(
                notification_id=notification_id,
                status=notification_doc.get("status"),
                channels=notification_doc.get("channels", []),
                channel_status=notification_doc.get("channel_status", {}),
                created_at=notification_doc.get("created_at"),
                sent_at=notification_doc.get("sent_at"),
                retry_count=notification_doc.get("retry_count", 0),
                error_message=notification_doc.get("error_message")
            ).dict()
        )
        return response.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notification status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch notification status")


@router.get("/user/{user_id}/in-app", response_model=dict)
async def get_user_notifications(
    user_id: str,
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get in-app notifications for a user
    
    Returns paginated list of notifications with unread count
    """
    try:
        query = InAppNotification.user_id == user_id
        
        if unread_only:
            query = query & (InAppNotification.is_read == False)
        
        # Get notifications
        notifications = await engine.find(
            InAppNotification,
            query,
            sort=InAppNotification.created_at.desc(),
            limit=limit,
            skip=skip
        )
        
        # Get total and unread counts
        total_count = await engine.count(InAppNotification, InAppNotification.user_id == user_id)
        unread_count = await engine.count(
            InAppNotification,
            InAppNotification.user_id == user_id,
            InAppNotification.is_read == False
        )
        
        notification_list = [
            InAppNotificationResponse(
                id=str(notif.id),
                user_id=notif.user_id,
                title=notif.title,
                message=notif.message,
                notification_type=notif.notification_type,
                is_read=notif.is_read,
                action_url=notif.action_url,
                action_label=notif.action_label,
                created_at=notif.created_at
            )
            for notif in notifications
        ]
        
        return success_response(
            data=NotificationListResponse(
                total=total_count,
                unread_count=unread_count,
                notifications=notification_list
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Error fetching user notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@router.put("/user/{user_id}/in-app/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    user_id: str,
    notification_id: str,
    engine: AIOEngine = Depends(get_engine)
):
    """
    Mark an in-app notification as read
    """
    try:
        from bson import ObjectId
        
        notification = await engine.find_one(
            InAppNotification,
            InAppNotification.id == ObjectId(notification_id),
            InAppNotification.user_id == user_id
        )
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await engine.save(notification)
        
        return success_response(
            message="Notification marked as read",
            data={"notification_id": notification_id, "is_read": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.put("/user/{user_id}/in-app/read-all", response_model=dict)
async def mark_all_notifications_read(
    user_id: str,
    engine: AIOEngine = Depends(get_engine)
):
    """
    Mark all in-app notifications as read for a user
    """
    try:
        # Use MongoDB update directly for better performance
        result = await engine.get_collection(InAppNotification).update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        return success_response(
            message=f"Marked {result.modified_count} notifications as read",
            data={"marked_count": result.modified_count}
        )
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notifications")


@router.get("/queue/info", response_model=dict)
async def get_queue_info():
    """
    Get current notification queue statistics
    
    **Admin endpoint** - shows queue health and pending jobs
    """
    try:
        queue_info = notification_queue.get_queue_info()
        health = notification_queue.health_check()
        
        response = success_response(
            data={
                "health": "healthy" if health else "unhealthy",
                "queue": queue_info
            }
        )
        return response.model_dump()
    except Exception as e:
        logger.error(f"Error fetching queue info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch queue information")
