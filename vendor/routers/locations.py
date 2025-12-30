from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.location import (
    VendorLocationCreateRequest,
    VendorLocationResponse,
    VendorLocationUpdateRequest,
)
from vendor.services.location_service import (
    create_location,
    list_locations,
    update_location,
)


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Locations"],
)


@router.post("/{vendor_id}/locations")
async def add_vendor_location(
    vendor_id: str,
    payload: VendorLocationCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    location, vendor = await create_location(
        engine=engine,
        vendor_id=vendor_id,
        payload=payload,
    )

    return success_response(
        message="Location added successfully",
        data={
            "location_id": str(location.id),
            "vendor_status": vendor.status,
        },
    )


@router.get("/{vendor_id}/locations")
async def get_vendor_locations(
    vendor_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    locations = await list_locations(engine, vendor_id)

    return success_response(
        data=[
            VendorLocationResponse(
                id=str(loc.id),
                name=loc.name,
                city=loc.city,
                state=loc.state,
                pincode=loc.pincode,
                latitude=loc.latitude,
                longitude=loc.longitude,
            )
            for loc in locations
        ]
    )



@router.patch("/{vendor_id}/locations/{location_id}")
async def update_vendor_location(
    vendor_id: str,
    location_id: str,
    payload: VendorLocationUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    location = await update_location(engine, vendor_id, location_id, payload)

    return success_response(
        message="Location updated",
        data={"location_id": str(location.id)},
    )
