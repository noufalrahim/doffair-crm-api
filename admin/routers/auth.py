from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from admin.schemas.auth import AdminLoginRequest, AdminLoginResponse, AdminSignupRequest, AdminSignupResponse, LoginData
from admin.services.auth_service import authenticate_admin, register_admin
from core.database import get_engine
from utils.response import success_response

router = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Auth"],
)

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    payload: AdminLoginRequest,
    engine: AIOEngine = Depends(get_engine),
):
    token, admin = await authenticate_admin(
        engine=engine,
        email=payload.email,
        password=payload.password,
    )

    return success_response(
        message="Login successful",
        data=LoginData(
            access_token=token,
            admin=admin
        )
    ).model_dump()


@router.post("/signup", response_model=AdminSignupResponse)
async def admin_signup(
    payload: AdminSignupRequest,
    engine: AIOEngine = Depends(get_engine),
):
    token, admin = await register_admin(
        engine=engine,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        is_super_admin=payload.is_super_admin,
    )

    return success_response(
        message="Admin created successfully",
        data=LoginData(
            access_token=token,
            admin=admin
        )
    ).model_dump()
