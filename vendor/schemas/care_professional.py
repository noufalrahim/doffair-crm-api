from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from core.enums import CareProfessionalRole


class CareProfessionalCreateRequest(BaseModel):
    location_id: str
    vertical_id: str
    name: str
    email: EmailStr
    phone: str = Field(..., examples=["9876543210"])
    password: str = Field(..., min_length=8)
    role: CareProfessionalRole = CareProfessionalRole.STAFF



class CareProfessionalUpdateRequest(BaseModel):
    name: Optional[str] = None
    location_id: Optional[str] = None
    role: Optional[CareProfessionalRole] = None
    is_active: Optional[bool] = None


class CareProfessionalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    role: CareProfessionalRole
    location_id: str
    vertical_id: str
    is_active: bool
    created_at: str
    
    # Enriched fields
    email: Optional[str] = None
    phone: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
