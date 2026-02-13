from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from core.media import build_image_list   # ✅ IMAGE HELPER
from utils.response import success_response
from bson import ObjectId


from vendor.schemas.vertical import (
    VendorVerticalSelectRequest,
    VendorVerticalUpdateRequest,
    VendorVerticalResponse,
)
from vendor.services.vertical_service import (
    select_verticals,
    update_vendor_vertical,
    delete_vendor_vertical,
)
from admin.models.vertical import Vertical
from vendor.models.vendor_vertical import VendorVertical


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Verticals"],
)

# ---------------------------------------------------------
# Select Vendor Verticals (CREATE)
# ---------------------------------------------------------

@router.post("/verticals")
async def select_vendor_verticals_api(
    payload: VendorVerticalSelectRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await select_verticals(
        engine=engine,
        vendor_id=vendor_id,
        vertical_ids=payload.vertical_ids,
    )

    # Fetch admin verticals with images
    verticals_data = await engine.find(
        Vertical,
        Vertical.id.in_(
            [ObjectId(v_id) for v_id in payload.vertical_ids]
        ),
    )

    return success_response(
        message="Verticals selected successfully",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
            "verticals": [
                {
                    "vertical_id": str(v.id),
                    "name": v.display_name,
                    "images": build_image_list(v.image_blob_paths),  # ✅ IMAGES
                }
                for v in verticals_data
            ],
        },
    )


# ---------------------------------------------------------
# Update Vendor Vertical (Activate / Deactivate)
# ---------------------------------------------------------

@router.patch("/verticals/{vertical_id}")
async def update_vendor_vertical_api(
    vertical_id: str,
    payload: VendorVerticalUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    await update_vendor_vertical(
        engine,
        vendor_id,
        vertical_id,
        payload.is_active,
    )

    # Fetch admin vertical for images
    vertical_def = await engine.find_one(
        Vertical,
        Vertical.id == ObjectId(vertical_id),
    )

    return success_response(
        message="Vertical updated",
        data={
            "vertical_id": vertical_id,
            "is_active": payload.is_active,
            "images": (
                build_image_list(vertical_def.image_blob_paths)
                if vertical_def
                else []
            ),
        },
    )



# ---------------------------------------------------------
# Delete Vendor Vertical
# ---------------------------------------------------------

@router.delete("/verticals/{vertical_id}")
async def delete_vendor_vertical_api(
    vertical_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    await delete_vendor_vertical(
        engine,
        vendor_id,
        vertical_id,
    )

    return success_response(
        message="Vertical deleted successfully",
    )


# ---------------------------------------------------------
# Get Vendor Vertical by ID (simpler path)
# ---------------------------------------------------------

router_general = APIRouter(
    prefix="/vendor/verticals",
    tags=["Vendor Verticals"],
)

@router_general.get("/{vertical_id}")
async def get_vendor_vertical_api(
    vertical_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    # 1. Fetch VendorVertical status
    vst = await engine.find_one(
        VendorVertical,
        (VendorVertical.vendor_id == vendor_id)
        & (VendorVertical.vertical_id == vertical_id),
    )

    if not vst:
         raise HTTPException(
            status_code=404,
            detail="Vertical not found or not selected by vendor",
        )

    # 2. Fetch Admin Vertical details
    v_def = await engine.find_one(
        Vertical,
        Vertical.id == ObjectId(vertical_id),
    )
    
    if not v_def:
         raise HTTPException(status_code=404, detail="Vertical definition not found")

    # 3. Return combined response
    return success_response(
        data=VendorVerticalResponse(
            id=str(v_def.id),
            name=v_def.display_name,
            description=v_def.description,
            images=build_image_list(v_def.image_blob_paths),
            is_active=vst.is_active,
        ).model_dump()
    )
