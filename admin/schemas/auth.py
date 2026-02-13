from pydantic import BaseModel, EmailStr # type: ignore
from admin.schemas.admin import AdminResponse


from schemas.common import APIResponse


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


class AdminLoginResponse(APIResponse):
    data: LoginData


class AdminSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    is_super_admin: bool = False


class AdminSignupResponse(APIResponse):
    data: LoginData
