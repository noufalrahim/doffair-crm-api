import logging
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from odmantic import AIOEngine
from notifications.models.preferences import NotificationIdempotency
from core.database import get_engine

engine = get_engine()

logger = logging.getLogger(__name__)


class IdempotencyService:
    def __init__(self, db_engine: AIOEngine = engine):
        self.engine = db_engine
    
    @staticmethod
    def generate_key(event_id: str, recipient_id: str, channel: str) -> str:
        raw = f"{event_id}:{recipient_id}:{channel}"
        return hashlib.sha256(raw.encode()).hexdigest()
    
    async def check_and_record(
        self,
        event_id: str,
        recipient_id: str,
        channel: str,
        notification_id: Optional[str] = None
    ) -> bool:
        try:
            idempotency_key = self.generate_key(event_id, recipient_id, channel)
            
            existing = await self.engine.find_one(
                NotificationIdempotency,
                NotificationIdempotency.idempotency_key == idempotency_key
            )
            
            if existing:
                logger.info(
                    f"⚠️ Duplicate notification detected: "
                    f"event={event_id}, recipient={recipient_id}, channel={channel}"
                )
                return False
            
            record = NotificationIdempotency(
                idempotency_key=idempotency_key,
                event_id=event_id,
                recipient_id=recipient_id,
                channel=channel,
                notification_id=notification_id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            await self.engine.save(record)
            logger.debug(f"✅ Recorded idempotency key: {idempotency_key[:16]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check idempotency: {str(e)}")
            return True
    
    async def cleanup_expired(self):
        try:
            from pymongo import DeleteMany
            
            result = await self.engine.get_collection(NotificationIdempotency).delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {result.deleted_count} expired idempotency records")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired idempotency records: {str(e)}")


idempotency_service = IdempotencyService()
