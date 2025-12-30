from pydantic import BaseModel, EmailStr
from core.enums import VendorStatus


class VendorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class VendorLoginResponse(BaseModel):
    vendor_id: str
    status: VendorStatus
    access_token: str
    token_type: str = "bearer"
