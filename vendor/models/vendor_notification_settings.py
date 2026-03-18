from typing import Optional
from odmantic import Model, EmbeddedModel, Field

class NotificationTriggerSetting(EmbeddedModel):
    send_email: bool = True
    send_sms: bool = True
    offset_minutes: Optional[int] = None

class VendorNotificationSettings(Model):
    vendor_id: str = Field(unique=True)
    booking_created: NotificationTriggerSetting = Field(default_factory=NotificationTriggerSetting)
    booking_confirmed: NotificationTriggerSetting = Field(default_factory=NotificationTriggerSetting)
    booking_cancelled: NotificationTriggerSetting = Field(default_factory=NotificationTriggerSetting)
    upcoming_appointment: NotificationTriggerSetting = Field(default_factory=NotificationTriggerSetting)
    
    model_config = {
        "collection": "vendor_notification_settings",
        "parse_doc_with_default_factories": True
    }
