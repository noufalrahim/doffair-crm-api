from pydantic import BaseModel, EmailStr, Field


class UserSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, examples=["John Doe"])
    phone: str = Field(..., examples=["9876543210"])
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    user_id: str
    name: str
    email: str
    access_token: str
    token_type: str = "bearer"
