from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from core.enums import BookingStatus

class WalkinBookingCreate(BaseModel):
    # Customer info (Mandatory)
    customer_name: str
    customer_email: str
    customer_phone: str
    
    # Pet info (Optional)
    pet_name: Optional[str] = None
    pet_gender: Optional[str] = None
    pet_height: Optional[float] = None
    pet_weight: Optional[float] = None
    pet_breed: Optional[str] = None
    pet_vaccinated: Optional[bool] = None
    pet_age: Optional[int] = None
    pet_about: Optional[str] = None
    
    # Booking details (Mandatory)
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    services: List[str] = [] # List of service names or descriptions (Legacy/Fallback)
    booking_date: datetime
    status: BookingStatus = BookingStatus.CONFIRMED
    final_amount: float = Field(0.0, ge=0)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v
