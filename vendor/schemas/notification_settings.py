from pydantic import BaseModel
from typing import Optional

class NotificationTriggerSchema(BaseModel):
    send_email: bool = True
    send_sms: bool = True
    offset_minutes: Optional[int] = None

class VendorNotificationSettingsUpdate(BaseModel):
    booking_created: Optional[NotificationTriggerSchema] = None
    booking_confirmed: Optional[NotificationTriggerSchema] = None
    booking_cancelled: Optional[NotificationTriggerSchema] = None
    upcoming_appointment: Optional[NotificationTriggerSchema] = None

class VendorNotificationSettingsResponse(BaseModel):
    id: str
    vendor_id: str
    booking_created: NotificationTriggerSchema
    booking_confirmed: NotificationTriggerSchema
    booking_cancelled: NotificationTriggerSchema
    upcoming_appointment: NotificationTriggerSchema
