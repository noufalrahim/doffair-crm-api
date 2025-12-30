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


@router.post("/{vendor_id}/amenities")
async def upsert_amenities(
    vendor_id: str,
    payload: VendorAmenityUpsertRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        record = await upsert_vendor_amenities(engine, vendor_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Amenities saved successfully",
        data={
            "location_id": record.location_id,
            "service_type_id": record.service_type_id,
            "amenity_codes": record.amenity_codes,
        },
    )
