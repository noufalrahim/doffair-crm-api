from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from notifications.enums import NotificationChannel, NotificationPriority


class RecipientInfo(BaseModel):
    """Recipient contact information"""
    user_id: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    
    @validator('phone', 'whatsapp')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('Phone numbers must include country code starting with +')
        return v


class NotificationRequest(BaseModel):
    """Request schema for sending notifications"""
    
    # Target channels
    channels: List[NotificationChannel] = Field(
        ...,
        description="Channels to send notification: email, sms, whatsapp, in_app",
        min_items=1
    )
    
    # Recipient
    recipient: RecipientInfo = Field(
        ...,
        description="Recipient contact information"
    )
    
    # Content
    template_id: str = Field(
        ...,
        description="Template identifier like 'BOOKING_CONFIRMED', 'ORDER_PLACED'",
        example="BOOKING_CONFIRMED"
    )
    
    subject: Optional[str] = Field(
        None,
        description="Subject line for email/in-app notification",
        example="Your booking has been confirmed!"
    )
    
    message: Optional[str] = Field(
        None,
        description="Fallback message if template not found",
        example="Your booking #12345 has been confirmed for 2026-01-15"
    )
    
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template variables/data",
        example={
            "booking_id": "BK12345",
            "service_name": "Dog Grooming",
            "booking_date": "2026-01-15T10:00:00",
            "vendor_name": "Happy Paws Salon"
        }
    )
    
    # Metadata
    event_type: Optional[str] = Field(
        None,
        description="Event type: booking, order, payment, system",
        example="booking"
    )
    
    priority: NotificationPriority = Field(
        default=NotificationPriority.MEDIUM,
        description="Notification priority"
    )
    
    # Reference
    reference_type: Optional[str] = Field(
        None,
        description="Type of referenced entity",
        example="booking"
    )
    
    reference_id: Optional[str] = Field(
        None,
        description="ID of referenced entity",
        example="679abc123def456"
    )
    
    # Scheduling (future feature)
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Schedule notification for future delivery"
    )
    
    @validator('channels', pre=True)
    def validate_channels(cls, v):
        if isinstance(v, str):
            v = [v]
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "channels": ["email", "sms", "in_app"],
                "recipient": {
                    "user_id": "679f1a2b3c4d5e6f7a8b9c0d",
                    "email": "user@example.com",
                    "phone": "+919876543210"
                },
                "template_id": "BOOKING_CONFIRMED",
                "subject": "Booking Confirmed!",
                "data": {
                    "booking_id": "BK12345",
                    "service_name": "Dog Grooming",
                    "booking_date": "2026-01-15T10:00:00",
                    "vendor_name": "Happy Paws Salon"
                },
                "event_type": "booking",
                "priority": "high",
                "reference_type": "booking",
                "reference_id": "679abc123def456"
            }
        }


class NotificationResponse(BaseModel):
    """Response after queuing notification"""
    notification_id: str
    status: str
    message: str
    queued_at: datetime
    channels: List[str]


class NotificationStatusResponse(BaseModel):
    """Response for checking notification status"""
    notification_id: str
    status: str
    channels: List[str]
    channel_status: Dict[str, str]
    created_at: datetime
    sent_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None


class InAppNotificationCreate(BaseModel):
    """Schema for creating in-app notifications"""
    user_id: str
    title: str
    message: str
    notification_type: str = "system"
    icon: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None


class InAppNotificationResponse(BaseModel):
    """Response schema for in-app notifications"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response for listing notifications"""
    total: int
    unread_count: int
    notifications: List[InAppNotificationResponse]
