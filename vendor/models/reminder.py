"""
Reminder model for custom follow-up reminders
Vendors can schedule reminders for customers via different channels
"""
from datetime import datetime
from odmantic import Model, Field
from typing import Optional, List
from bson import ObjectId


class Reminder(Model):
    """
    Custom reminder for customer follow-ups
    Supports multiple notification channels and scheduling
    """
    # Relationships
    vendor_id: str
    customer_id: str
    
    # Reminder Details
    title: str
    message: str
    reminder_type: str
    
    # Notification Channels (at least one must be True)
    send_sms: bool = True
    send_email: bool = False
    send_whatsapp: bool = False
    send_in_app: bool = True
    
    # Status Tracking
    status: str = "PENDING"
    is_active: bool = True
    
    # STRING FIELDS - Use empty string defaults instead of Optional[str] for ODMantic 1.0.0
    booking_id: str = ""
    error_message: str = ""
    sms_status: str = ""
    email_status: str = ""
    whatsapp_status: str = ""
    notes: str = ""
    
    # DATETIME FIELDS - Must be at the end
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "reminders",
        "indexes": [
            # Primary lookups
            {"fields": ["vendor_id"]},
            {"fields": ["customer_id"]},
            {"fields": ["booking_id"]},
            
            # Scheduling queries (most important for cron jobs)
            {"fields": ["status", "scheduled_at"]},
            {"fields": ["vendor_id", "status"]},
            
            # Customer timeline
            {"fields": ["customer_id", "scheduled_at"]},
            
            # Filtering
            {"fields": ["vendor_id", "reminder_type"]},
            {"fields": ["created_at"]},
        ],
    }
