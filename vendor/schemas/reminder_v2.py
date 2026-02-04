"""
Reminder schemas for API requests and responses
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class CreateReminderRequest(BaseModel):
    """Request schema for creating a reminder"""
    booking_id: str = Field(..., description="Booking ID to link reminder to")
    title: str = Field(..., min_length=1, max_length=200, description="Reminder title")
    message: str = Field(..., min_length=1, max_length=1000, description="Reminder message")
    reminder_type: str = Field(
        default="FOLLOW_UP",
        description="Type: FOLLOW_UP, MEDICATION, APPOINTMENT, REPEAT_SERVICE, GENERAL"
    )
    scheduled_at: datetime = Field(..., description="When to send the reminder")
    
    # Notification channels
    send_sms: bool = Field(default=True, description="Send via SMS")
    send_email: bool = Field(default=False, description="Send via Email")
    send_whatsapp: bool = Field(default=False, description="Send via WhatsApp")
    send_in_app: bool = Field(default=True, description="Send in-app notification")
    
    notes: Optional[str] = Field(default=None, max_length=500, description="Internal notes")
    
    @field_validator('reminder_type')
    def validate_reminder_type(cls, v):
        valid_types = ["FOLLOW_UP", "MEDICATION", "APPOINTMENT", "REPEAT_SERVICE", "GENERAL"]
        if v not in valid_types:
            raise ValueError(f"Invalid reminder_type. Must be one of: {valid_types}")
        return v
    
    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v < datetime.utcnow():
            raise ValueError("scheduled_at must be in the future")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "69830c42b18ec9ac59765093",
                "title": "Follow-up Checkup Reminder",
                "message": "Please visit for your follow-up checkup scheduled for tomorrow at 10 AM",
                "reminder_type": "FOLLOW_UP",
                "scheduled_at": "2026-02-15T10:00:00",
                "send_sms": True,
                "send_email": True,
                "send_whatsapp": False,
                "send_in_app": True,
                "notes": "Patient recovering from surgery"
            }
        }


class ReminderResponse(BaseModel):
    """Response schema for reminder data"""
    id: str
    vendor_id: str
    customer_id: str
    booking_id: str
    
    title: str
    message: str
    reminder_type: str
    
    send_sms: bool
    send_email: bool
    send_whatsapp: bool
    send_in_app: bool
    
    status: str
    error_message: str
    
    sms_status: str
    email_status: str
    whatsapp_status: str
    
    notes: str
    is_active: bool
    
    scheduled_at: datetime
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "69830c42b18ec9ac59765093",
                "vendor_id": "69804efc422c93604361e316",
                "customer_id": "offline_9876543210",
                "booking_id": "69830c42b18ec9ac59765093",
                "title": "Follow-up Checkup Reminder",
                "message": "Please visit for your follow-up checkup",
                "reminder_type": "FOLLOW_UP",
                "send_sms": True,
                "send_email": True,
                "send_whatsapp": False,
                "send_in_app": True,
                "status": "PENDING",
                "error_message": "",
                "sms_status": "",
                "email_status": "",
                "whatsapp_status": "",
                "notes": "Patient recovering from surgery",
                "is_active": True,
                "scheduled_at": "2026-02-15T10:00:00",
                "sent_at": None,
                "created_at": "2026-02-04T10:00:00",
                "updated_at": "2026-02-04T10:00:00"
            }
        }


class ReminderListResponse(BaseModel):
    """Response schema for list of reminders"""
    total: int
    reminders: list[ReminderResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "reminders": [
                    {
                        "id": "69830c42b18ec9ac59765093",
                        "title": "Follow-up Checkup",
                        "reminder_type": "FOLLOW_UP",
                        "scheduled_at": "2026-02-15T10:00:00",
                        "status": "PENDING"
                    }
                ]
            }
        }


class UpdateReminderRequest(BaseModel):
    """Request schema for updating a reminder"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=1000)
    scheduled_at: Optional[datetime] = None
    send_sms: Optional[bool] = None
    send_email: Optional[bool] = None
    send_whatsapp: Optional[bool] = None
    send_in_app: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("scheduled_at must be in the future")
        return v
