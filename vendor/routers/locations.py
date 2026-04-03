from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from bson import ObjectId
from vendor.models.vendor import Vendor
from vendor.models.care_professional import CareProfessional
from vendor.models.vendor_service import VendorService

from vendor.schemas.location import (
    VendorLocationCreateRequest,
    VendorLocationResponse,
    VendorLocationUpdateRequest,
)
from vendor.services.location_service import (
    create_location,
    list_locations,
    update_location,
    set_default_location,
    delete_location,
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
            "is_default": location.is_default,
        },
    )


@router.get("/locations")
async def get_vendor_locations(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    locations = await list_locations(engine, vendor_id)
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    legal_name = vendor.legal_name if vendor else None

    active_staff = await engine.find(
        CareProfessional,
        (CareProfessional.vendor_id == vendor_id) & (CareProfessional.is_active == True),
    )
    active_services = await engine.find(
        VendorService,
        (VendorService.vendor_id == vendor_id) & (VendorService.is_active == True),
    )

    staff_counts = Counter(str(s.location_id) for s in active_staff if getattr(s, "location_id", None))
    service_counts = Counter(str(s.location_id) for s in active_services if getattr(s, "location_id", None))

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
                is_default=loc.is_default,
                staff_count=staff_counts.get(str(loc.id), 0),
                service_count=service_counts.get(str(loc.id), 0),
                legal_name=legal_name,
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
        data={"location_id": str(location.id), "is_default": location.is_default},
    )


@router.post("/locations/{location_id}/set-default")
async def set_vendor_default_location(
    location_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Set a specific location as the default for this vendor."""
    vendor_id = token["vendor_id"]

    location = await set_default_location(engine, vendor_id, location_id)

    return success_response(
        message="Default location updated",
        data={"location_id": str(location.id), "is_default": location.is_default},
    )


@router.delete("/locations/{location_id}")
async def delete_vendor_location(
    location_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    await delete_location(engine, vendor_id, location_id)

    return success_response(message="Location deleted successfully")
