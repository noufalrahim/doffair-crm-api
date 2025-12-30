from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from admin.schemas.auth import AdminLoginRequest, AdminLoginResponse
from admin.services.auth_service import authenticate_admin
from core.database import get_engine

router = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Auth"],
)


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    payload: AdminLoginRequest,
    engine: AIOEngine = Depends(get_engine),
):
    token = await authenticate_admin(
        engine=engine,
        email=payload.email,
        password=payload.password,
    )

    return AdminLoginResponse(access_token=token)
