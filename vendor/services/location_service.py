from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from core.enums import VendorStatus
from vendor.utils.guards import ensure_vendor_editable


async def create_location(
    engine: AIOEngine,
    vendor_id: str,
    payload,
):
    try:
        vendor_oid = ObjectId(vendor_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vendor id",
        )

    vendor = await engine.find_one(Vendor, Vendor.id == vendor_oid)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    location = VendorLocation(
        vendor_id=vendor_id,
        name=payload.name,
        address_line_1=payload.address_line_1,
        address_line_2=payload.address_line_2,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        country=payload.country,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    await engine.save(location)

    # Update onboarding status
    vendor.status = VendorStatus.LOCATION_ADDED
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)

    return location, vendor


async def list_locations(
    engine: AIOEngine,
    vendor_id: str,
):
    locations = await engine.find(
        VendorLocation,
        VendorLocation.vendor_id == vendor_id,
    )
    return locations


async def update_location(
    engine,
    vendor_id: str,
    location_id: str,
    payload,
):
    location = await engine.find_one(
        VendorLocation,
        VendorLocation.id == ObjectId(location_id),
    )

    if not location or location.vendor_id != vendor_id:
        raise HTTPException(status_code=404, detail="Location not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(location, field, value)

    location.updated_at = datetime.utcnow()
    await engine.save(location)
    return location

