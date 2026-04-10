from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, Any
from core.enums import VendorStatus


class VendorSignupRequest(BaseModel):
    phone: str = Field(..., examples=["9876543210"])
    email: EmailStr
    password: str = Field(..., min_length=8)


class VendorBasicInfoRequest(BaseModel):
    legal_name: str = Field(..., min_length=3)

    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None
    profileImage: Optional[str] = None
    coverPhoto: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_snake_case(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map variations for profileImage
            for key in ["profile_image", "profileimage", "profile_photo", "profilephoto"]:
                if key in data and "profileImage" not in data:
                    data["profileImage"] = data.pop(key)
            
            # Map variations for coverPhoto
            for key in ["cover_photo", "coverphoto", "cover_image", "coverimage"]:
                if key in data and "coverPhoto" not in data:
                    data["coverPhoto"] = data.pop(key)
        return data


class VendorStatusResponse(BaseModel):
    vendor_id: str
    status: VendorStatus


class VendorBasicInfoUpdateRequest(BaseModel):
    legal_name: Optional[str] = None
    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None
    profileImage: Optional[str] = None
    coverPhoto: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_snake_case(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map variations for profileImage
            for key in ["profile_image", "profileimage", "profile_photo", "profilephoto"]:
                if key in data and "profileImage" not in data:
                    data["profileImage"] = data.pop(key)
            
            # Map variations for coverPhoto
            for key in ["cover_photo", "coverphoto", "cover_image", "coverimage"]:
                if key in data and "coverPhoto" not in data:
                    data["coverPhoto"] = data.pop(key)
        return data


class VendorOnboardingProgressResponse(BaseModel):
    vendor_id: str
    
    # Progress status
    mobile_verified: bool
    email_verified: bool
    basic_info_added: bool
    verticals_added: bool
    location_added: bool
    bank_account_added: bool
    
    # Summary
    percentage_completed: float
    pending_steps: list[str]


class OtpSendRequest(BaseModel):
    phone: str
    email: EmailStr


class OtpVerifyRequest(BaseModel):
    phone: str
    email: EmailStr
    sms_otp: str
    email_otp: str
