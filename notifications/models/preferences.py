from odmantic import Model, Field
from typing import Dict, Optional
from datetime import datetime


class UserNotificationPreferences(Model):
    user_id: str = Field(index=True)
    email_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=True)
    whatsapp_enabled: bool = Field(default=True)
    in_app_enabled: bool = Field(default=True)
    
    event_preferences: Dict[str, bool] = Field(default_factory=dict)
    
    quiet_hours_enabled: bool = Field(default=False)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "user_notification_preferences"
    }


class NotificationIdempotency(Model):
    idempotency_key: str = Field(index=True, unique=True)
    event_id: str
    recipient_id: str
    channel: str
    notification_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    model_config = {
        "collection": "notification_idempotency"
    }
