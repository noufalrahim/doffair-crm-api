from datetime import datetime
from odmantic import Model, Field
from typing import Optional
from core.enums import BookingStatus


class Booking(Model):
    """
    Booking model - User books a service from vendor
    """
    # References
    user_id: str
    vendor_id: str
    service_id: str
    service_type_id: str
    location_id: str
    
    # Cached information for quick access
    user_name: str
    user_phone: str
    user_email: str
    
    vendor_name: str
    vendor_phone: str
    vendor_email: str
    
    service_name: str
    service_type_name: str
    
    # Booking details
    booking_date: datetime  # When the service will be performed
    delivery_mode: str  # CENTER, HOME, BOTH
    
    # Address (for HOME delivery)
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_pincode: Optional[str] = None
    
    # Pricing
    base_amount: float
    discount_amount: float = 0.0
    final_amount: float
    
    # Payment reference
    payment_id: Optional[str] = None  # Links to Payment model
    
    # Status tracking
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    
    # Vendor action
    vendor_notes: Optional[str] = None  # Vendor can add notes
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Completion
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    # Pet/Dog Details (for pet services)
    pet_name: Optional[str] = None
    pet_type: Optional[str] = None  # dog, cat, bird, etc.
    pet_breed: Optional[str] = None
    pet_age: Optional[int] = None  # in months
    pet_weight: Optional[float] = None  # in kg
    pet_gender: Optional[str] = None  # male, female
    pet_medical_conditions: Optional[str] = None
    pet_special_notes: Optional[str] = None
    pet_images: list[str] = []  # Image URLs/blob paths for pet photos
    
    # Offline Booking Support
    is_offline: bool = False
    customer_age: int = 0
    customer_gender: Optional[str] = None
    customer_address_full: Optional[str] = None
    customer_city_stored: Optional[str] = None
    customer_pincode_stored: Optional[str] = None
    customer_blood_group: Optional[str] = None
    customer_allergies: Optional[str] = None
    customer_medical_conditions: Optional[str] = None
    customer_notes: Optional[str] = None
    payment_mode: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "bookings",
        "indexes": [
            {"fields": ["user_id"]},
            {"fields": ["vendor_id"]},
            {"fields": ["service_id"]},
            {"fields": ["status"]},
            {"fields": ["booking_date"]},
            {"fields": ["created_at"]},
            # For vendor dashboard
            {"fields": ["vendor_id", "status"]},
            # For user's bookings
            {"fields": ["user_id", "status"]},
            # For offline bookings
            {"fields": ["is_offline"]},
            {"fields": ["vendor_id", "is_offline"]},
            {"fields": ["vendor_id", "user_phone"]},  # Customer phone lookup
        ],
    }
