"""
In-App Notification Handler
Creates notifications in the database for user's notification center
"""
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
import logging
import json
import redis.asyncio as redis
from core.config import settings

from notifications.handlers.base import BaseNotificationHandler
from notifications.models.notification import InAppNotification
from odmantic import AIOEngine

logger = logging.getLogger(__name__)


class InAppHandler(BaseNotificationHandler):
    """
    Handles in-app notifications by creating records in database
    These appear in user's notification center
    """
    
    def __init__(self, engine: AIOEngine):
        super().__init__()
        self.engine = engine
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """Validate user_id is present"""
        return bool(notification_data.get("user_id"))
    
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create in-app notification in database
        
        Returns success immediately since it's just a DB write
        """
        try:
            # Validate
            if not self.validate_recipient(notification_data):
                raise ValueError("user_id is required for in-app notifications")
            
            user_id = notification_data["user_id"]
            notification_id = notification_data.get("notification_id")
            
            # Prepare content
            title = notification_data.get("subject", "New Notification")
            message = await self.prepare_content(notification_data)
            
            # Create in-app notification record
            in_app_notif = InAppNotification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_data.get("event_type") or "system",
                icon=None,
                action_url=None,
                action_label=None,
                data=notification_data.get("data", {}),
                reference_type=notification_data.get("reference_type"),
                reference_id=notification_data.get("reference_id"),
                is_read=False
            )
            
            # Save to database
            saved = await self.engine.save(in_app_notif)
            
            metadata = {
                "in_app_notification_id": str(saved.id),
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.log_success(notification_id, metadata)
            
            # Broadcast via Redis for WebSockets
            try:
                broadcast_data = {
                    "user_id": user_id,
                    "notification": {
                        "id": str(saved.id),
                        "title": title,
                        "message": message,
                        "notification_type": in_app_notif.notification_type,
                        "created_at": saved.created_at.isoformat(),
                        "data": in_app_notif.data
                    }
                }
                await self.redis_client.publish("notifications_broadcast", json.dumps(broadcast_data))
                logger.info(f"📣 Published real-time notification for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Failed to publish real-time notification: {str(e)}")
            
            return {
                "success": True,
                "message": "In-app notification created successfully",
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Failed to create in-app notification: {str(e)}"
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
