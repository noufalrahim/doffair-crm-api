from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine
from typing import List

from core.database import get_engine
from core.security import require_admin
from core.media import build_image_list  # ✅ IMAGE HELPER

from admin.schemas.service_type import (
    ServiceTypeCreateResponse,
    ServiceTypeCreate,
    ServiceTypeResponse,
    ServiceTypeListResponse,
)
from admin.services.service_type_service import (
    create_service_type,
    list_service_types,
    toggle_service_type_status,
)

router = APIRouter(
    prefix="/admin/service-types",
    tags=["Admin - Service Types"],
)

# ---------------------------------------------------------
# Create Service Type
# ---------------------------------------------------------

@router.post(
    "",
    response_model=ServiceTypeCreateResponse,
    dependencies=[Depends(require_admin)],
)
async def create_service(
    payload: ServiceTypeCreate,
    engine: AIOEngine = Depends(get_engine),
):
    service = await create_service_type(engine, payload)

    return ServiceTypeCreateResponse(
        success=True,
        success_message="Service type created successfully",
        data=ServiceTypeResponse(
            id=str(service.id),
            code=service.code,
            display_name=service.display_name,
            description=service.description,
            mode=service.mode,
            is_active=service.is_active,
            images=build_image_list(service.image_blob_paths),  # ✅ IMAGES
        ),
    )


# ---------------------------------------------------------
# List Service Types
# ---------------------------------------------------------

@router.get(
    "",
    response_model=ServiceTypeListResponse,
    dependencies=[Depends(require_admin)],
)
async def get_services(
    include_inactive: bool = Query(default=True),
    engine: AIOEngine = Depends(get_engine),
):
    services = await list_service_types(engine, include_inactive)

    return ServiceTypeListResponse(
        success=True,
        success_message="Services retrieved successfully",
        data=[
            ServiceTypeResponse(
                id=str(s.id),
                code=s.code,
                display_name=s.display_name,
                description=s.description,
                mode=s.mode,
                is_active=s.is_active,
                images=build_image_list(s.image_blob_paths),  # ✅ IMAGES
            )
            for s in services
        ],
    )


# ---------------------------------------------------------
# Activate / Deactivate Service Type
# ---------------------------------------------------------

@router.patch(
    "/{service_type_id}/status",
    response_model=ServiceTypeResponse,
    dependencies=[Depends(require_admin)],
)
async def update_service_status(
    service_type_id: str,
    is_active: bool,
    engine: AIOEngine = Depends(get_engine),
):
    service = await toggle_service_type_status(engine, service_type_id, is_active)

    return ServiceTypeResponse(
        id=str(service.id),
        code=service.code,
        display_name=service.display_name,
        description=service.description,
        mode=service.mode,
        is_active=service.is_active,
        images=build_image_list(service.image_blob_paths),  # ✅ IMAGES
    )
