from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_admin
from utils.response import success_response

from admin.schemas.amenity import (
    AmenityCreateRequest,
    AmenityResponse,
    AmenityCreateResponse,
    AmenityListResponse,
    AmenityMapResponse,
    VerticalAmenityMapRequest,
)
from admin.services.amenity_service import (
    create_amenity,
    list_amenities,
    map_amenities_to_vertical,
)
from utils.response import success_response


router = APIRouter(
    prefix="/admin/amenities",
    tags=["Admin - Amenities"],
)


@router.post("", response_model=AmenityCreateResponse, dependencies=[Depends(require_admin)])
async def create_amenity_api(
    payload: AmenityCreateRequest,
    engine: AIOEngine = Depends(get_engine),
):
    amenity = await create_amenity(engine, payload)

    return success_response(
        message="Amenity created successfully",
        data=AmenityResponse(
            code=amenity.code,
            display_name=amenity.display_name,
            description=amenity.description,
            icon=amenity.icon,
            is_active=amenity.is_active,
        ),
    ).model_dump()


@router.get("", response_model=AmenityListResponse, dependencies=[Depends(require_admin)])
async def list_amenities_api(
    engine: AIOEngine = Depends(get_engine),
):
    amenities = await list_amenities(engine)

    return success_response(
        data=[
            AmenityResponse(
                code=a.code,
                display_name=a.display_name,
                description=a.description,
                icon=a.icon,
                is_active=a.is_active,
            )
            for a in amenities
        ]
    ).model_dump()


@router.post(
    "/verticals/{vertical_id}",
    response_model=AmenityMapResponse,
    dependencies=[Depends(require_admin)],
)
async def map_amenities_api(
    vertical_id: str,
    payload: VerticalAmenityMapRequest,
    engine: AIOEngine = Depends(get_engine),
):
    await map_amenities_to_vertical(
        engine,
        vertical_id,
        payload.amenity_codes,
    )

    return success_response(
        message="Amenities mapped to vertical",
        data={
            "vertical_id": vertical_id,
            "amenity_codes": payload.amenity_codes,
        },
    ).model_dump()
