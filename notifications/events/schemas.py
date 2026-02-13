from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from notifications.events.types import EventType, EventSource


class EventPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: EventSource
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator("data")
    @classmethod
    def validate_data_not_empty(cls, v):
        if not v:
            raise ValueError("Event data cannot be empty")
        return v
    
    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Event ID cannot be empty")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class BookingEventData(BaseModel):
    booking_id: str
    user_id: str
    vendor_id: str
    vertical: str
    scheduled_at: datetime
    pet_name: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    total_amount: Optional[float] = None
    cancellation_reason: Optional[str] = None
    previous_scheduled_at: Optional[datetime] = None
    
    @field_validator("booking_id", "user_id", "vendor_id", "vertical")
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Required field cannot be empty")
        return v


class PaymentEventData(BaseModel):
    payment_id: str
    booking_id: str
    user_id: str
    amount: float
    currency: str = "INR"
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    failure_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    
    @field_validator("payment_id", "booking_id", "user_id")
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Required field cannot be empty")
        return v
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class UserEventData(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    reset_token: Optional[str] = None
    verification_code: Optional[str] = None
    
    @field_validator("user_id", "email")
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Required field cannot be empty")
        return v


class VendorEventData(BaseModel):
    vendor_id: str
    email: str
    business_name: str
    name: Optional[str] = None
    phone: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    @field_validator("vendor_id", "email", "business_name")
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Required field cannot be empty")
        return v
