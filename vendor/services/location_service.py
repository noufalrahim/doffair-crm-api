from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from core.enums import VendorStatus
from vendor.utils.guards import ensure_vendor_editable

from vendor.models.care_professional import CareProfessional
from vendor.models.vendor_service import VendorService


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

    # Check if this is the vendor's first location
    existing_count = await engine.count(
        VendorLocation,
        VendorLocation.vendor_id == vendor_id,
    )
    is_first_location = existing_count == 0

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
        is_default=is_first_location,  # First location is default
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

    update_data = payload.dict(exclude_unset=True)

    # If setting is_default to True, unset all others first
    if update_data.get("is_default") is True:
        await _unset_other_defaults(engine, vendor_id, location_id)

    for field, value in update_data.items():
        setattr(location, field, value)

    location.updated_at = datetime.utcnow()
    await engine.save(location)
    return location


async def set_default_location(
    engine: AIOEngine,
    vendor_id: str,
    location_id: str,
):
    """Set a specific location as the default, unsetting all others."""
    location = await engine.find_one(
        VendorLocation,
        VendorLocation.id == ObjectId(location_id),
    )

    if not location or location.vendor_id != vendor_id:
        raise HTTPException(status_code=404, detail="Location not found")

    # Unset all other defaults
    await _unset_other_defaults(engine, vendor_id, location_id)

    # Set this one as default
    location.is_default = True
    location.updated_at = datetime.utcnow()
    await engine.save(location)
    return location


async def _unset_other_defaults(
    engine: AIOEngine,
    vendor_id: str,
    exclude_location_id: str,
):
    """Set is_default=False for all vendor locations except the excluded one."""
    all_locations = await engine.find(
        VendorLocation,
        VendorLocation.vendor_id == vendor_id,
    )
    for loc in all_locations:
        if str(loc.id) != exclude_location_id and loc.is_default:
            loc.is_default = False
            loc.updated_at = datetime.utcnow()
            await engine.save(loc)


async def delete_location(
    engine: AIOEngine,
    vendor_id: str,
    location_id: str,
):
    """
    Deletes a location if it has no active staff or services.
    If the deleted location was the default, reassigns default to another location.
    """
    location = await engine.find_one(
        VendorLocation,
        VendorLocation.id == ObjectId(location_id),
        VendorLocation.vendor_id == vendor_id,
    )

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Check for active staff
    active_staff = await engine.count(
        CareProfessional,
        (CareProfessional.location_id == location_id) & (CareProfessional.is_active == True),
    )
    if active_staff > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location with active staff. Please move or deactivate staff first.",
        )

    # Check for active services
    active_services = await engine.count(
        VendorService,
        (VendorService.location_id == location_id) & (VendorService.is_active == True),
    )
    if active_services > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location with active services. Please move or deactivate services first.",
        )

    was_default = location.is_default

    await engine.delete(location)

    # If it was default, try to set another location as default
    if was_default:
        remaining_locations = await engine.find(
            VendorLocation,
            VendorLocation.vendor_id == vendor_id,
            sort=VendorLocation.created_at.asc(),
        )
        if remaining_locations:
            new_default = remaining_locations[0]
            new_default.is_default = True
            new_default.updated_at = datetime.utcnow()
            await engine.save(new_default)

    return True
