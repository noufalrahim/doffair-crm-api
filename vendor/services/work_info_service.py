from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from typing import Optional


async def update_work_info(
    engine: AIOEngine,
    vendor_id: str,
    payload,
    location_id: Optional[str] = None,
):
    """Create or update work-related info on the vendor document."""
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

    # If location_id is provided, update the specific location
    if location_id:
        location = await engine.find_one(
            VendorLocation, 
            (VendorLocation.id == ObjectId(location_id)) & (VendorLocation.vendor_id == vendor_id)
        )
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        
        for field, value in payload.dict(exclude_unset=True).items():
            if hasattr(location, field):
                setattr(location, field, value)
        
        location.updated_at = datetime.utcnow()
        await engine.save(location)
        return location

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(vendor, field, value)

    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)
    return vendor


async def get_work_info(
    engine: AIOEngine,
    vendor_id: str,
    location_id: Optional[str] = None,
):
    """Get work-related info from the vendor document."""
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

    # If location_id is provided, get info from specific location
    if location_id:
        location = await engine.find_one(
            VendorLocation, 
            (VendorLocation.id == ObjectId(location_id)) & (VendorLocation.vendor_id == vendor_id)
        )
        if location:
            return {
                "vendor_id": str(vendor.id),
                "home_service": location.home_service,
                "centre_service": location.centre_service,
                "home_service_radius": location.home_service_radius,
                "overall_rating": vendor.overall_rating, # Rating is usually across the vendor
                "work_experience": location.work_experience if location.work_experience is not None else vendor.work_experience,
            }

    return {
        "vendor_id": str(vendor.id),
        "home_service": vendor.home_service,
        "centre_service": vendor.centre_service,
        "home_service_radius": vendor.home_service_radius,
        "overall_rating": vendor.overall_rating,
        "work_experience": vendor.work_experience,
    }
