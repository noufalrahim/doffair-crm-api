"""
Offline booking schemas - Simplified version
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from core.enums import ServiceDeliveryMode


class CreateOfflineBookingSimple(BaseModel):
    """Create offline booking - all customer data in one request"""
    # Customer info
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_phone: str = Field(..., min_length=10, max_length=15)
    customer_email: Optional[EmailStr] = None
    customer_age: int = Field(default=0, ge=0, le=150)
    customer_gender: Optional[str] = None
    customer_address: Optional[str] = None
    customer_city: Optional[str] = None
    customer_pincode: Optional[str] = None
    customer_blood_group: Optional[str] = None
    customer_allergies: Optional[str] = None
    customer_medical_conditions: Optional[str] = None
    customer_notes: Optional[str] = None
    
    # Service info
    service_id: str
    service_type_id: str
    location_id: str
    service_name: str
    service_type_name: str
    
    # Booking details
    booking_date: datetime
    delivery_mode: ServiceDeliveryMode = ServiceDeliveryMode.CENTER
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_pincode: Optional[str] = None
    
    # Payment
    final_amount: float = Field(..., ge=0)
    payment_mode: str = "CASH"
    vendor_notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "John Doe",
                "customer_phone": "9876543210",
                "customer_email": "john@example.com",
                "customer_age": 35,
                "customer_gender": "Male",
                "customer_city": "Mumbai",
                "service_id": "507f1f77bcf86cd799439011",
                "service_type_id": "507f1f77bcf86cd799439012",
                "location_id": "507f1f77bcf86cd799439013",
                "service_name": "Blood Test",
                "service_type_name": "Lab Services",
                "booking_date": "2026-02-10T10:00:00",
                "final_amount": 1500.0,
                "payment_mode": "CASH"
            }
        }


class OfflineBookingResponse(BaseModel):
    """Offline booking response"""
    id: str
    vendor_id: str
    
    # Customer
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    customer_age: int
    customer_gender: Optional[str]
    
    # Service
    service_name: str
    service_type_name: str
    
    # Booking
    booking_date: datetime
    delivery_mode: ServiceDeliveryMode
    final_amount: float
    payment_mode: Optional[str]
    status: str
    
    vendor_notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
