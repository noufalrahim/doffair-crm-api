from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from core.database import get_engine
from core.security import require_admin, security_scheme, HTTPAuthorizationCredentials
from typing import List
from admin.schemas.admin import AdminCreateRequest, AdminCreateResponse, AdminResponse, AdminMeData, AdminMeResponse, AdminPermissionsUpdateRequest
from admin.services.admin_service import add_new_admin, get_admin_by_id
from utils.response import success_response, APIResponse
from admin.models.admin import Admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin - Admin Management"],
)

@router.get("/admins", response_model=APIResponse)
async def list_admins(
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    """
    List all admins.
    """
    admins = await engine.find(Admin)
    return success_response(
        message="Admins retrieved successfully",
        data=[AdminResponse.model_validate(a).model_dump() for a in admins]
    ).model_dump()

@router.post("/admins", response_model=AdminCreateResponse)
async def create_admin(
    payload: AdminCreateRequest,
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    """
    Create a new admin.
    """
    admin = await add_new_admin(engine, payload)
    
    return success_response(
        message="Admin created successfully",
        data=AdminResponse.model_validate(admin)
    ).model_dump()

@router.patch("/admins/{admin_id}/permissions", response_model=AdminCreateResponse)
async def update_admin_permissions(
    admin_id: str,
    payload: AdminPermissionsUpdateRequest,
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    """
    Update admin permissions.
    """
    admin = await get_admin_by_id(engine, admin_id)
    admin.permissions = payload.permissions
    await engine.save(admin)
    
    return success_response(
        message="Permissions updated successfully",
        data=AdminResponse.model_validate(admin)
    ).model_dump()

@router.get("/me", response_model=AdminMeResponse)
async def get_admin_profile(
    current_token: dict = Depends(require_admin),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get current admin's profile information from JWT token
    """
    admin_id = current_token["sub"]
    admin = await get_admin_by_id(engine, admin_id)
    
    return success_response(
        message="Admin profile retrieved successfully",
        data=AdminMeData(
            **AdminResponse.model_validate(admin).model_dump(),
            access_token=credentials.credentials
        )
    ).model_dump()
