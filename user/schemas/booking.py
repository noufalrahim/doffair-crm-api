from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from core.enums import BookingStatus, PaymentStatus, ServiceDeliveryMode


# ---------------------------------------------------------
# User: Create Booking
# ---------------------------------------------------------

class UserSummary(BaseModel):
    name: str
    phone: str
    email: str
    image: Optional[str] = None

class PetSummary(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    medical_conditions: Optional[str] = None
    special_notes: Optional[str] = None
    images: Optional[list[str]] = None

class CreateBookingRequest(BaseModel):
    """
    User creates a booking for a service
    """
    service_id: str
    booking_date: datetime = Field(..., description="When the service will be performed")
    delivery_mode: str = Field(..., description="'In-Center', 'At Home', or 'BOTH'")
    
    # For HOME delivery
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_pincode: Optional[str] = None
    
    # Pet Details (for pet services)
    pet_name: Optional[str] = Field(None, description="Pet's name")
    pet_type: Optional[str] = Field(None, description="dog, cat, bird, etc.")
    pet_breed: Optional[str] = Field(None, description="Pet breed")
    pet_age: Optional[int] = Field(None, description="Pet age in months")
    pet_weight: Optional[float] = Field(None, description="Pet weight in kg")
    pet_gender: Optional[str] = Field(None, description="male or female")
    pet_medical_conditions: Optional[str] = Field(None, description="Any medical conditions")
    pet_special_notes: Optional[str] = Field(None, description="Special instructions for pet care")
    pet_images: Optional[list[str]] = Field(None, description="URLs or paths to pet images")


class CreateBookingResponse(BaseModel):
    """
    Response after creating booking (before payment)
    """
    id: str
    service_name: str
    vendor_name: Optional[str] = None
    booking_date: datetime
    final_amount: float
    status: BookingStatus
    payment_required: bool = True
    message: str


# ---------------------------------------------------------
# Payment Initiation
# ---------------------------------------------------------

class InitiatePaymentRequest(BaseModel):
    """
    User initiates payment for a booking
    """
    id: str
    payment_method: str = "razorpay"


class InitiatePaymentResponse(BaseModel):
    """
    Response with payment gateway details
    """
    payment_id: str
    id: str
    amount: float
    currency: str = "INR"
    payment_gateway_order_id: str  # Razorpay order_id
    message: str


# ---------------------------------------------------------
# Payment Confirmation
# ---------------------------------------------------------

class ConfirmPaymentRequest(BaseModel):
    """
    User confirms payment was successful
    """
    id: str
    payment_id: str
    payment_gateway_payment_id: str  # Razorpay payment_id
    payment_gateway_signature: str   # Razorpay signature


class ConfirmPaymentResponse(BaseModel):
    """
    Response after payment confirmation
    """
    id: str
    payment_id: str
    status: BookingStatus
    message: str


# ---------------------------------------------------------
# Booking Responses
# ---------------------------------------------------------

class BookingResponse(BaseModel):
    """
    Detailed booking information
    """
    id: str
    vendor_name: Optional[str] = None
    vendor_phone: Optional[str] = None
    service_name: str
    service_type_name: str
    booking_date: datetime
    delivery_mode: ServiceDeliveryMode
    service_address: Optional[str] = None
    final_amount: float
    status: BookingStatus
    payment_status: Optional[str] = None
    vendor_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    
    # Nested Objects
    user: UserSummary
    pet: Optional[PetSummary] = None


# ---------------------------------------------------------
# Vendor Actions
# ---------------------------------------------------------

class ApproveBookingRequest(BaseModel):
    """
    Vendor approves a booking
    """
    notes: Optional[str] = Field(None, description="Optional notes for the booking")


class RejectBookingRequest(BaseModel):
    """
    Vendor rejects a booking (triggers refund)
    """
    rejection_reason: str = Field(..., min_length=10, description="Reason for rejection")


class VendorActionResponse(BaseModel):
    """
    Response after vendor approves/rejects
    """
    id: str
    status: BookingStatus
    message: str
    refund_initiated: bool = False
