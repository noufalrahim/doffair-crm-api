from datetime import datetime
from odmantic import Model, Field
from typing import Optional, Dict, List, Any
from notifications.enums import NotificationChannel, NotificationStatus, NotificationPriority


class NotificationLog(Model):
    """
    Tracks all notification requests and their delivery status
    Each notification can be sent across multiple channels
    """
    
    # Recipient Information
    user_id: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_whatsapp: Optional[str] = None
    
    # Notification Configuration
    channels: List[str]  # List of channels to send: ["email", "sms", "whatsapp", "in_app"]
    template_id: str  # Template identifier: "BOOKING_CONFIRMED", "ORDER_PLACED", etc.
    
    # Content & Data
    subject: Optional[str] = None  # For email/in-app
    message: Optional[str] = None  # Fallback message if template not found
    data: Dict[str, Any] = Field(default_factory=dict)  # Template variables
    
    # Metadata
    event_type: Optional[str] = None  # "booking", "order", "payment", etc.
    priority: NotificationPriority = NotificationPriority.MEDIUM
    
    # Status Tracking
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Channel-Specific Status (to track each channel independently)
    channel_status: Dict[str, str] = Field(default_factory=dict)
    # Example: {"email": "sent", "sms": "failed", "whatsapp": "pending"}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Error Handling
    retry_count: int = 0
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Scheduling (for future use)
    scheduled_at: Optional[datetime] = None
    
    # Reference IDs (for tracking)
    reference_type: Optional[str] = None  # "booking", "order", "payment"
    reference_id: Optional[str] = None  # ID of the booking/order/payment
    
    model_config = {
        "collection": "notification_logs"
    }


class InAppNotification(Model):
    """
    In-app notifications shown in user's notification center
    Separate model for fast queries and display
    """
    
    user_id: str
    vendor_id: Optional[str] = None
    
    # Content
    title: str
    message: str
    icon: Optional[str] = None  # Icon identifier or URL
    
    # Categorization
    notification_type: str  # "booking", "order", "system", "promotional"
    category: Optional[str] = None
    
    # Status
    is_read: bool = False
    is_archived: bool = False
    
    # Action
    action_url: Optional[str] = None  # Deep link or URL to navigate
    action_label: Optional[str] = None  # "View Booking", "See Details"
    
    # Metadata
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Reference
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    model_config = {
        "collection": "in_app_notifications"
    }
