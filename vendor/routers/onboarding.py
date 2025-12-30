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
)
from vendor.services.onboarding_service import (
    signup_vendor,
    update_basic_info,
    get_vendor_status,
    update_basic_info_partial,
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

@router.post("/{vendor_id}/basic-info")
async def vendor_basic_info(
    vendor_id: str,
    payload: VendorBasicInfoRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this vendor",
        )

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

@router.get("/{vendor_id}/status")
async def vendor_status(
    vendor_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    vendor = await get_vendor_status(engine, vendor_id)

    return success_response(
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        }
    )


# ---------------------------------------------------------
# Vendor Basic Info (UPDATE / PATCH)
# ---------------------------------------------------------

@router.patch("/{vendor_id}/basic-info")
async def update_vendor_basic_info(
    vendor_id: str,
    payload: VendorBasicInfoUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    vendor = await update_basic_info_partial(engine, vendor_id, payload)

    return success_response(
        message="Basic info updated",
        data={
            "vendor_id": vendor_id,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )



@router.post("/{vendor_id}/submit-for-review")
async def submit_for_review(
    vendor_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403)

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
