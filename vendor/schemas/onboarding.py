from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from core.enums import VendorStatus


class VendorSignupRequest(BaseModel):
    phone: str = Field(..., examples=["9876543210"])
    email: EmailStr
    password: str = Field(..., min_length=8)


class VendorBasicInfoRequest(BaseModel):
    legal_name: str = Field(..., min_length=3)

    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None


class VendorStatusResponse(BaseModel):
    vendor_id: str
    status: VendorStatus


class VendorBasicInfoUpdateRequest(BaseModel):
    legal_name: Optional[str] = None
    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None
