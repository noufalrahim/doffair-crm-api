from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.work_info import (
    VendorWorkInfoRequest,
    VendorWorkInfoUpdateRequest,
)
from typing import Optional
from vendor.services.work_info_service import (
    update_work_info,
    get_work_info,
)


router = APIRouter(
    prefix="/vendor",
    tags=["Vendor - Work Info"],
)


@router.put("/work-info")
async def create_or_update_work_info(
    payload: VendorWorkInfoRequest,
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Create or update work-related info for the vendor."""
    vendor_id = token["vendor_id"]
    vendor = await update_work_info(engine, vendor_id, payload, location_id=location_id)

    return success_response(
        message="Work info updated successfully",
        data={
            "vendor_id": str(vendor.id),
            "home_service": vendor.home_service,
            "centre_service": vendor.centre_service,
            "home_service_radius": vendor.home_service_radius,
            "overall_rating": vendor.overall_rating,
            "work_experience": vendor.work_experience,
        },
    )


@router.patch("/work-info")
async def patch_work_info(
    payload: VendorWorkInfoUpdateRequest,
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Partially update work-related info for the vendor."""
    vendor_id = token["vendor_id"]
    vendor = await update_work_info(engine, vendor_id, payload, location_id=location_id)

    return success_response(
        message="Work info updated successfully",
        data={
            "vendor_id": str(vendor.id),
            "home_service": vendor.home_service,
            "centre_service": vendor.centre_service,
            "home_service_radius": vendor.home_service_radius,
            "overall_rating": vendor.overall_rating,
            "work_experience": vendor.work_experience,
        },
    )


@router.get("/work-info")
async def get_vendor_work_info(
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Get work-related info for the vendor."""
    vendor_id = token["vendor_id"]
    work_info = await get_work_info(engine, vendor_id, location_id=location_id)

    return success_response(
        message="Work info retrieved successfully",
        data=work_info,
    )
