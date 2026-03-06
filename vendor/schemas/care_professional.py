from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from core.enums import CareProfessionalRole
from vendor.schemas.location import VendorLocationResponse


class UserResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: str
    phone: str
    is_active: bool
    is_verified: bool


class CareProfessionalCreateRequest(BaseModel):
    location_id: str
    vertical_id: str
    name: str
    email: EmailStr
    phone: str = Field(..., examples=["9876543210"])
    password: str = Field(..., min_length=8)
    role: CareProfessionalRole = CareProfessionalRole.STAFF
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    consultation_fee: Optional[float] = None
    license_number: Optional[str] = None
    profile_image: Optional[str] = Field(None, alias="profileImage")

    model_config = {
        "populate_by_name": True
    }


class CareProfessionalUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, examples=["Dr. John Doe"])
    email: Optional[EmailStr] = Field(None, examples=["john.doe@example.com"])
    phone: Optional[str] = Field(None, examples=["9876543210"])
    location_id: Optional[str] = None
    role: Optional[CareProfessionalRole] = None
    is_active: Optional[bool] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    consultation_fee: Optional[float] = None
    license_number: Optional[str] = None
    profile_image: Optional[str] = Field(None, alias="profileImage")

    model_config = {
        "populate_by_name": True
    }


class CareProfessionalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    role: CareProfessionalRole
    location_id: str
    vertical_id: str
    is_active: bool
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    consultation_fee: Optional[float] = None
    license_number: Optional[str] = None
    profile_image: Optional[str] = Field(None, alias="profileImage")
    created_at: str

    model_config = {
        "populate_by_name": True
    }
    
    # Enriched objects
    user: Optional[UserResponse] = None
    location: Optional[VendorLocationResponse] = None

    # Legacy enriched fields
    email: Optional[str] = None
    phone: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
