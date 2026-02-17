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


@router.post("/locations")
async def add_vendor_location(
    payload: VendorLocationCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

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


@router.get("/locations")
async def get_vendor_locations(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    locations = await list_locations(engine, vendor_id)

    return success_response(
        data=[
            VendorLocationResponse(
                id=str(loc.id),
                name=loc.name,
                address_line_1=loc.address_line_1,
                address_line_2=loc.address_line_2,
                city=loc.city,
                state=loc.state,
                pincode=loc.pincode,
                latitude=loc.latitude,
                longitude=loc.longitude,
            )
            for loc in locations
        ]
    )



@router.patch("/locations/{location_id}")
async def update_vendor_location(
    location_id: str,
    payload: VendorLocationUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    location = await update_location(engine, vendor_id, location_id, payload)

    return success_response(
        message="Location updated",
        data={"location_id": str(location.id)},
    )
