import logging
from typing import Optional
from datetime import datetime, time
from odmantic import AIOEngine
from notifications.models.preferences import UserNotificationPreferences
from notifications.enums import NotificationChannel
from notifications.events.types import EventType
from core.database import get_engine

engine = get_engine()

logger = logging.getLogger(__name__)


class PreferencesService:
    def __init__(self, db_engine: AIOEngine = engine):
        self.engine = db_engine
    
    async def get_preferences(self, user_id: str) -> Optional[UserNotificationPreferences]:
        try:
            prefs = await self.engine.find_one(
                UserNotificationPreferences,
                UserNotificationPreferences.user_id == user_id
            )
            
            if not prefs:
                prefs = UserNotificationPreferences(user_id=user_id)
                await self.engine.save(prefs)
                logger.info(f"✅ Created default preferences for user {user_id}")
            
            return prefs
            
        except Exception as e:
            logger.error(f"❌ Failed to get preferences for user {user_id}: {str(e)}")
            return None
    
    async def is_channel_enabled(self, user_id: str, channel: NotificationChannel) -> bool:
        try:
            prefs = await self.get_preferences(user_id)
            
            if not prefs:
                return True
            
            if channel == NotificationChannel.EMAIL:
                return prefs.email_enabled
            elif channel == NotificationChannel.SMS:
                return prefs.sms_enabled
            elif channel == NotificationChannel.WHATSAPP:
                return prefs.whatsapp_enabled
            elif channel == NotificationChannel.IN_APP:
                return prefs.in_app_enabled
            
            return True
            
        except Exception as e:
            logger.error(
                f"❌ Failed to check channel preference for user {user_id}, "
                f"channel {channel}: {str(e)}"
            )
            return True
    
    async def is_event_enabled(self, user_id: str, event_type: EventType) -> bool:
        try:
            prefs = await self.get_preferences(user_id)
            
            if not prefs or not prefs.event_preferences:
                return True
            
            return prefs.event_preferences.get(event_type.value, True)
            
        except Exception as e:
            logger.error(
                f"❌ Failed to check event preference for user {user_id}, "
                f"event {event_type.value}: {str(e)}"
            )
            return True
    
    async def is_in_quiet_hours(self, user_id: str) -> bool:
        try:
            prefs = await self.get_preferences(user_id)
            
            if not prefs or not prefs.quiet_hours_enabled:
                return False
            
            if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
                return False
            
            now = datetime.utcnow().time()
            start_time = time.fromisoformat(prefs.quiet_hours_start)
            end_time = time.fromisoformat(prefs.quiet_hours_end)
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:
                return now >= start_time or now <= end_time
            
        except Exception as e:
            logger.error(f"❌ Failed to check quiet hours for user {user_id}: {str(e)}")
            return False
    
    async def update_preferences(
        self,
        user_id: str,
        **updates
    ) -> Optional[UserNotificationPreferences]:
        try:
            prefs = await self.get_preferences(user_id)
            
            if not prefs:
                return None
            
            for key, value in updates.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            prefs.updated_at = datetime.utcnow()
            await self.engine.save(prefs)
            
            logger.info(f"✅ Updated preferences for user {user_id}")
            return prefs
            
        except Exception as e:
            logger.error(f"❌ Failed to update preferences for user {user_id}: {str(e)}")
            return None


preferences_service = PreferencesService()
