from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor


async def update_work_info(
    engine: AIOEngine,
    vendor_id: str,
    payload,
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

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(vendor, field, value)

    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)
    return vendor


async def get_work_info(
    engine: AIOEngine,
    vendor_id: str,
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

    return {
        "vendor_id": str(vendor.id),
        "home_service": vendor.home_service,
        "centre_service": vendor.centre_service,
        "home_service_radius": vendor.home_service_radius,
        "overall_rating": vendor.overall_rating,
        "work_experience": vendor.work_experience,
    }
