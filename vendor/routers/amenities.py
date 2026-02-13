from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.amenity import VendorAmenityUpsertRequest
from vendor.services.amenity_service import upsert_vendor_amenities


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Amenities"],
)


@router.post("/amenities")
async def upsert_amenities(
    payload: VendorAmenityUpsertRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    try:
        record = await upsert_vendor_amenities(engine, vendor_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Amenities saved successfully",
        data={
            "location_id": record.location_id,
            "vertical_id": record.vertical_id,
            "amenity_codes": record.amenity_codes,
        },
    )
