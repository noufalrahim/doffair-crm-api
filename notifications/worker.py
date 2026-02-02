"""
Background worker tasks for processing notifications
Consumes jobs from Redis queue and dispatches to channel handlers
"""
import asyncio
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import logging

from core.config import settings
from notifications.models.notification import NotificationLog
from notifications.enums import NotificationStatus, NotificationChannel
from notifications.handlers.email_handler import EmailHandler
from notifications.handlers.sms_handler import SMSHandler
from notifications.handlers.whatsapp_handler import WhatsAppHandler
from notifications.handlers.inapp_handler import InAppHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_notification(notification_id: str):
    """
    Main worker task: Process a notification by sending through all requested channels
    
    Called by RQ worker when job is picked from queue
    Uses MongoDB direct updates to avoid datetime validation issues
    """
    client = None
    try:
        logger.info(f"🔄 Processing notification {notification_id}")
        
        # Connect to database
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
        
        # Fetch notification directly from MongoDB (avoid datetime validation)
        notification_doc = await engine.get_collection(NotificationLog).find_one(
            {"_id": ObjectId(notification_id)}
        )
        
        if not notification_doc:
            logger.error(f"❌ Notification {notification_id} not found in database")
            return
        
        # Update status to PROCESSING using MongoDB directly
        await engine.get_collection(NotificationLog).update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"status": NotificationStatus.PROCESSING.value}}
        )
        
        # Extract notification data
        channels = notification_doc.get("channels", [])
        user_id = notification_doc.get("user_id")
        
        notification_data = {
            "notification_id": notification_id,
            "user_id": user_id,
            "recipient_email": notification_doc.get("recipient_email"),
            "recipient_phone": notification_doc.get("recipient_phone"),
            "recipient_whatsapp": notification_doc.get("recipient_whatsapp"),
            "subject": notification_doc.get("subject"),
            "message": notification_doc.get("message"),
            "data": notification_doc.get("data", {}),
            "template_id": notification_doc.get("template_id"),
            "event_type": notification_doc.get("event_type"),
            "reference_type": notification_doc.get("reference_type"),
            "reference_id": notification_doc.get("reference_id"),
        }
        
        logger.info(f"📤 Sending through channels: {channels}")
        
        # Initialize handlers
        handlers = {
            NotificationChannel.EMAIL.value: EmailHandler(),
            NotificationChannel.SMS.value: SMSHandler(),
            NotificationChannel.WHATSAPP.value: WhatsAppHandler(),
            NotificationChannel.IN_APP.value: InAppHandler(engine),
        }
        
        # Send through each channel
        channel_results = {}
        all_success = True
        
        for channel in channels:
            handler = handlers.get(channel)
            
            if not handler:
                logger.warning(f"⚠️ No handler found for channel: {channel}")
                channel_results[channel] = NotificationStatus.FAILED.value
                all_success = False
                continue
            
            try:
                # Send through channel
                result = await handler.send(notification_data)
                
                if result.get("success"):
                    channel_results[channel] = NotificationStatus.SENT.value
                    logger.info(f"✅ {channel}: {result.get('message')}")
                else:
                    channel_results[channel] = NotificationStatus.FAILED.value
                    all_success = False
                    logger.error(f"❌ {channel}: {result.get('message')}")
                    
            except Exception as e:
                channel_results[channel] = NotificationStatus.FAILED.value
                all_success = False
                logger.error(f"❌ {channel} failed: {str(e)}")
        
        # Update notification status using MongoDB directly (avoid datetime validation)
        final_status = NotificationStatus.SENT if all_success else NotificationStatus.FAILED
        update_data = {
            "status": final_status.value,
            "channel_status": channel_results,
            "sent_at": datetime.utcnow() if all_success else None
        }
        
        if not all_success:
            update_data["error_message"] = "One or more channels failed"
        
        await engine.get_collection(NotificationLog).update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": update_data}
        )
        
        if all_success:
            logger.info(f"✅ Notification {notification_id} sent successfully through all channels")
        else:
            logger.warning(f"⚠️ Notification {notification_id} partially sent. Check channel_status")
        
    except Exception as e:
        logger.error(f"❌ Error processing notification {notification_id}: {str(e)}")
        
        # Update to failed status using MongoDB directly
        if client:
            try:
                engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
                await engine.get_collection(NotificationLog).update_one(
                    {"_id": ObjectId(notification_id)},
                    {
                        "$set": {
                            "status": NotificationStatus.FAILED.value,
                            "error_message": str(e),
                            "failed_at": datetime.utcnow()
                        },
                        "$inc": {"retry_count": 1}
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update error status: {str(update_error)}")
        
        raise  # Re-raise for RQ retry mechanism
        
    finally:
        if client:
            client.close()


# Sync wrapper for RQ (RQ doesn't support async directly)
def process_notification_sync(notification_id: str):
    """
    Synchronous wrapper for async worker task
    RQ requires sync functions, so we run the async task in event loop
    """
    asyncio.run(process_notification(notification_id))
