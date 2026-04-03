from pydantic import BaseModel, Field
from typing import Optional


class VendorLocationCreateRequest(BaseModel):
    name: str = Field(..., min_length=3)
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"

    latitude: float
    longitude: float


class VendorLocationResponse(BaseModel):
    id: str
    name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    is_default: bool = False
    staff_count: int = 0
    service_count: int = 0
    legal_name: Optional[str] = None



class VendorLocationUpdateRequest(BaseModel):
    name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
