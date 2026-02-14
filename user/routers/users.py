from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from pydantic import BaseModel

from core.database import get_engine
from user.models.user import User
from utils.response import success_response


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)



class CheckUserRequest(BaseModel):
    phone: str | None = None
    email: str | None = None


@router.post("/check-phone")
async def check_phone_exists(
    payload: CheckUserRequest,
    engine: AIOEngine = Depends(get_engine),
):
    """Check if a mobile number already exists in the users collection"""
    if not payload.phone:
        return success_response(data={"exists": False})
        
    user = await engine.find_one(User, User.phone == payload.phone)

    return success_response(
        data={"exists": user is not None},
    )


@router.post("/check")
async def check_user_exists(
    payload: CheckUserRequest,
    engine: AIOEngine = Depends(get_engine),
):
    """Check if a user exists with the given phone or email"""
    if not payload.phone and not payload.email:
        return success_response(data={"exists": False})
    
    criteria = None
    if payload.phone and payload.email:
        criteria = (User.phone == payload.phone) | (User.email == payload.email)
    elif payload.phone:
        criteria = User.phone == payload.phone
    elif payload.email:
        criteria = User.email == payload.email
    
    user = await engine.find_one(User, criteria)

    return success_response(
        data={"exists": user is not None},
    )
