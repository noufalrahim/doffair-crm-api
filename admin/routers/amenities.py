from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_admin
from utils.response import success_response

from admin.schemas.amenity import (
    AmenityCreateRequest,
    ServiceTypeAmenityMapRequest,
)
from admin.services.amenity_service import (
    create_amenity,
    list_amenities,
    map_amenities_to_service_type,
)


router = APIRouter(
    prefix="/admin/amenities",
    tags=["Admin - Amenities"],
)


@router.post("", dependencies=[Depends(require_admin)])
async def create_amenity_api(
    payload: AmenityCreateRequest,
    engine: AIOEngine = Depends(get_engine),
):
    amenity = await create_amenity(engine, payload)

    return success_response(
        message="Amenity created successfully",
        data={
            "code": amenity.code,
            "display_name": amenity.display_name,
            "is_active": amenity.is_active,
        },
    )


@router.get("", dependencies=[Depends(require_admin)])
async def list_amenities_api(
    engine: AIOEngine = Depends(get_engine),
):
    amenities = await list_amenities(engine)

    return success_response(
        data=[
            {
                "code": a.code,
                "display_name": a.display_name,
                "description": a.description,
                "icon": a.icon,
                "is_active": a.is_active,
            }
            for a in amenities
        ]
    )


@router.post(
    "/service-types/{service_type_id}",
    dependencies=[Depends(require_admin)],
)
async def map_amenities_api(
    service_type_id: str,
    payload: ServiceTypeAmenityMapRequest,
    engine: AIOEngine = Depends(get_engine),
):
    await map_amenities_to_service_type(
        engine,
        service_type_id,
        payload.amenity_codes,
    )

    return success_response(
        message="Amenities mapped to service type",
        data={
            "service_type_id": service_type_id,
            "amenity_codes": payload.amenity_codes,
        },
    )
