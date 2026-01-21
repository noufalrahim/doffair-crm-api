from enum import Enum


class NotificationChannel(str, Enum):
    """Supported notification channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
