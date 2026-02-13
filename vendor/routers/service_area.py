from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.service_area import ServiceAreaUpsertRequest
from vendor.services.service_area_service import upsert_service_area


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Service Area"],
)


@router.post("/service-area")
async def configure_service_area(
    payload: ServiceAreaUpsertRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    try:
        area = await upsert_service_area(engine, vendor_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Service area configured",
        data={
            "service_id": area.service_id,
            "area_type": area.area_type,
            "radius_km": area.radius_km,
            "pincodes": area.pincodes,
        },
    )
