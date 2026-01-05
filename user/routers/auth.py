from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from utils.response import success_response
from user.schemas.auth import UserSignupRequest, UserLoginRequest, UserLoginResponse
from user.services.auth_service import signup_user, login_user


router = APIRouter(
    prefix="/user/auth",
    tags=["User Authentication"],
)


@router.post("/signup")
async def user_signup(
    payload: UserSignupRequest,
    engine: AIOEngine = Depends(get_engine),
):
    """
    User signup - Create a new user account
    """
    user = await signup_user(engine, payload)
    
    return success_response(
        message="User account created successfully",
        data={
            "user_id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
        },
    )


@router.post("/login")
async def user_login(
    payload: UserLoginRequest,
    engine: AIOEngine = Depends(get_engine),
):
    """
    User login - Get JWT token
    """
    user, access_token = await login_user(engine, payload)
    
    return UserLoginResponse(
        user_id=str(user.id),
        name=user.name,
        email=user.email,
        access_token=access_token,
        token_type="bearer",
    )
