from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from core.media import build_image_set   # ✅ IMAGE HELPER
from vendor.models.vendor import Vendor
from utils.response import success_response
from bson import ObjectId

from vendor.schemas.onboarding import (
    VendorBasicInfoUpdateRequest,
    VendorSignupRequest,
    VendorBasicInfoRequest,
    VendorOnboardingProgressResponse,
)
from vendor.services.onboarding_service import (
    signup_vendor,
    update_basic_info,
    get_vendor_status,
    update_basic_info_partial,
    get_vendor_onboarding_progress,
)

from core.enums import VendorStatus
from datetime import datetime   

router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding"],
)

# ---------------------------------------------------------
# Vendor Signup (NO AUTH)
# ---------------------------------------------------------

@router.post("/signup")
async def vendor_signup(
    payload: VendorSignupRequest,
    engine: AIOEngine = Depends(get_engine),
):
    vendor = await signup_vendor(engine, payload)

    return success_response(
        message="Vendor signup successful",
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )


# ---------------------------------------------------------
# Vendor Basic Info (CREATE)
# ---------------------------------------------------------

@router.post("/basic-info")
async def vendor_basic_info(
    payload: VendorBasicInfoRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

    vendor = await update_basic_info(engine, vendor_id, payload)

    return success_response(
        message="Basic information saved successfully",
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )


# ---------------------------------------------------------
# Vendor Onboarding Status
# ---------------------------------------------------------

@router.get("/status")
async def vendor_status(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

    vendor = await get_vendor_status(engine, vendor_id)

    return success_response(
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        }
    )


@router.get("/progress", response_model=dict)
async def get_onboarding_progress(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Get vendor onboarding progress (percentage and pending steps)
    """
    vendor_id = token.get("vendor_id")
    if not vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Vendor ID not found in token",
        )

    progress = await get_vendor_onboarding_progress(engine, vendor_id)

    return success_response(
        message="Onboarding progress retrieved successfully",
        data=progress
    ).model_dump()



# ---------------------------------------------------------
# Vendor Basic Info (UPDATE / PATCH)
# ---------------------------------------------------------

@router.patch("/basic-info")
async def update_vendor_basic_info(
    payload: VendorBasicInfoUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await update_basic_info_partial(engine, vendor_id, payload)

    return success_response(
        message="Basic info updated",
        data={
            "vendor_id": vendor_id,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )



@router.post("/submit-for-review")
async def submit_for_review(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404)

    if vendor.status != VendorStatus.SERVICES_CONFIGURED:
        raise HTTPException(
            status_code=400,
            detail="Vendor is not ready for review",
        )

    vendor.status = VendorStatus.UNDER_REVIEW
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)

    return success_response(
        message="Vendor submitted for review",
        data={"status": vendor.status},
    )
