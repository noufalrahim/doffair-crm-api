from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from core.enums import ServiceDeliveryMode

class BookingStatusUpdate(BaseModel):
    status: str

class UserSummary(BaseModel):
    name: str = "Unknown"
    phone: str = "Unknown"
    email: str = "Unknown"
    image: Optional[str] = None

class PetSummary(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    images: List[str] = []
    
    # Enriched Details
    about_me: Optional[str] = None
    height: Optional[float] = None # Normalised to cm or similar if possible, or just value
    nature: Optional[str] = None
    energy_level: Optional[str] = None
    behavior: Optional[str] = None
    vaccinated: Optional[bool] = None
    vaccination_validated: Optional[bool] = None
    vaccination_date: Optional[datetime] = None
    
class ServiceSummary(BaseModel):
    id: Optional[str] = None
    name: str
    final_price: float = 0.0
    discount: float = 0.0
    duration_minutes: int = 0
    status: Optional[str] = None
    
class VendorBookingResponse(BaseModel):
    id: str
    booking_date: datetime
    status: str
    service_name: str
    services: List[ServiceSummary] = []
    service_type_name: str
    delivery_mode: ServiceDeliveryMode
    final_amount: float
    vendor_notes: Optional[str] = None
    created_at: datetime
    is_offline: bool = False
    
    # Nested Objects
    user: UserSummary
    pet: Optional[PetSummary] = None
