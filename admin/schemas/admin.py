from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from typing import Optional, Annotated

# Custom type for handling ObjectId to string conversion
PyObjectId = Annotated[str, BeforeValidator(str)]

from schemas.common import APIResponse


class AdminCreateRequest(BaseModel):
    name: str = Field(..., examples=["John Doe"])
    email: EmailStr = Field(..., examples=["admin@example.com"])
    password: str = Field(..., examples=["securepassword123"])
    is_super_admin: bool = False

class AdminResponse(BaseModel):
    id: PyObjectId
    name: str
    email: EmailStr
    is_active: bool
    is_super_admin: bool

    class Config:
        from_attributes = True

class AdminMeData(AdminResponse):
    access_token: str

class AdminMeResponse(APIResponse):
    data: AdminMeData

class AdminCreateResponse(APIResponse):
    data: AdminResponse
