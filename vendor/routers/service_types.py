from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from core.media import build_image_list   # ✅ IMAGE HELPER
from utils.response import success_response
from bson import ObjectId


from vendor.schemas.service_type import (
    VendorServiceTypeSelectRequest,
    VendorServiceTypeUpdateRequest,
)
from vendor.services.service_type_service import (
    select_service_types,
    update_vendor_service_type,
)
from admin.models.service_type import ServiceType  # ✅ for image fetch


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Service Types"],
)

# ---------------------------------------------------------
# Select Vendor Service Types (CREATE)
# ---------------------------------------------------------

@router.post("/service-types")
async def select_vendor_service_types(
    payload: VendorServiceTypeSelectRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await select_service_types(
        engine=engine,
        vendor_id=vendor_id,
        service_type_ids=payload.service_type_ids,
    )

    # Fetch admin service types with images
    service_types = await engine.find(
        ServiceType,
        ServiceType.id.in_(
            [ObjectId(st_id) for st_id in payload.service_type_ids]
        ),
    )

    return success_response(
        message="Service types selected successfully",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
            "service_types": [
                {
                    "service_type_id": str(st.id),
                    "name": st.display_name,
                    "images": build_image_list(st.image_blob_paths),  # ✅ IMAGES
                }
                for st in service_types
            ],
        },
    )


# ---------------------------------------------------------
# Update Vendor Service Type (Activate / Deactivate)
# ---------------------------------------------------------

@router.patch("/service-types/{service_type_id}")
async def update_vendor_service_type_api(
    service_type_id: str,
    payload: VendorServiceTypeUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    await update_vendor_service_type(
        engine,
        vendor_id,
        service_type_id,
        payload.is_active,
    )

    # Fetch admin service type for images
    service_type = await engine.find_one(
        ServiceType,
        ServiceType.id == engine._id_type(service_type_id),
    )

    return success_response(
        message="Service type updated",
        data={
            "service_type_id": service_type_id,
            "is_active": payload.is_active,
            "images": (
                build_image_list(service_type.image_blob_paths)
                if service_type
                else []
            ),
        },
    )
