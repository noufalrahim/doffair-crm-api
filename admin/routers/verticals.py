from fastapi import APIRouter, Depends, Query, status
from odmantic import AIOEngine
from typing import List

from core.database import get_engine
from core.security import require_admin
# from core.media import build_image_list  # Removed if not needed or if it causes issues with image_blob_paths direct list

from admin.schemas.vertical import (
    VerticalCreateResponse,
    VerticalCreate,
    VerticalUpdate,
    VerticalResponse,
    VerticalListResponse,
    VerticalSingleResponse,
)
from admin.services.vertical_service import (
    create_vertical,
    list_verticals,
    get_vertical_by_id,
    update_vertical,
    toggle_vertical_status,
    delete_vertical,
)
from schemas.common import APIResponse
from utils.response import success_response

router = APIRouter(
    prefix="/admin/verticals",
    tags=["Admin - Verticals"],
)

def format_vertical_response(service):
    return VerticalResponse(
        id=str(service.id),
        code=service.code,
        display_name=service.display_name,
        description=service.description,
        mode=service.mode,
        is_active=service.is_active,
        image_blob_paths=service.image_blob_paths,
        url=service.url,
        icon=service.icon,
        priority=service.priority,
    )

# ---------------------------------------------------------
# Create Service Type
# ---------------------------------------------------------

@router.post(
    "",
    response_model=VerticalCreateResponse,
    dependencies=[Depends(require_admin)],
)
async def create_vertical_api(
    payload: VerticalCreate,
    engine: AIOEngine = Depends(get_engine),
):
    vertical = await create_vertical(engine, payload)

    return success_response(
        message="Vertical created successfully",
        data=format_vertical_response(vertical),
    ).model_dump()


# ---------------------------------------------------------
# List Service Types
# ---------------------------------------------------------

@router.get(
    "",
    response_model=VerticalListResponse,
    dependencies=[Depends(require_admin)],
)
async def get_verticals(
    include_inactive: bool = Query(default=True),
    engine: AIOEngine = Depends(get_engine),
):
    verticals = await list_verticals(engine, include_inactive)

    return success_response(
        message="Verticals retrieved successfully",
        data=[format_vertical_response(v) for v in verticals],
    ).model_dump()


# ---------------------------------------------------------
# Get Single Service Type
# ---------------------------------------------------------

@router.get(
    "/{vertical_id}",
    response_model=VerticalSingleResponse,
    dependencies=[Depends(require_admin)],
)
async def get_vertical(
    vertical_id: str,
    engine: AIOEngine = Depends(get_engine),
):
    vertical = await get_vertical_by_id(engine, vertical_id)
    return success_response(
        message="Vertical retrieved successfully",
        data=format_vertical_response(vertical)
    ).model_dump()


# ---------------------------------------------------------
# Update Service Type
# ---------------------------------------------------------

@router.put(
    "/{vertical_id}",
    response_model=VerticalSingleResponse,
    dependencies=[Depends(require_admin)],
)
async def update_vertical_api(
    vertical_id: str,
    payload: VerticalUpdate,
    engine: AIOEngine = Depends(get_engine),
):
    vertical = await update_vertical(engine, vertical_id, payload)
    return success_response(
        message="Vertical updated successfully",
        data=format_vertical_response(vertical)
    ).model_dump()


# ---------------------------------------------------------
# Activate / Deactivate Service Type
# ---------------------------------------------------------

@router.patch(
    "/{vertical_id}/status",
    response_model=VerticalSingleResponse,
    dependencies=[Depends(require_admin)],
)
async def update_vertical_status(
    vertical_id: str,
    is_active: bool,
    engine: AIOEngine = Depends(get_engine),
):
    vertical = await toggle_vertical_status(engine, vertical_id, is_active)
    return success_response(
        message="Vertical status updated successfully",
        data=format_vertical_response(vertical)
    ).model_dump()


# ---------------------------------------------------------
# Delete Service Type
# ---------------------------------------------------------

@router.delete(
    "/{vertical_id}",
    response_model=APIResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_vertical_api(
    vertical_id: str,
    engine: AIOEngine = Depends(get_engine),
):
    await delete_vertical(engine, vertical_id)
    return success_response(
        message="Vertical deleted successfully",
    ).model_dump()
