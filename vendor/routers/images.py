from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
from odmantic import AIOEngine
from bson import ObjectId

from core.database import get_engine
from core.security import require_vendor
from core.image_utils import validate_image
from core.image_pipeline import generate_variants
from core.storage import upload_blob
from core.media import upload_and_process_image
from utils.response import success_response

from vendor.models.vendor_service import VendorService
from vendor.models.vendor import Vendor


router = APIRouter(
    prefix="/vendor/assets",
    tags=["Vendor Assets"],
)

# =========================================================
# Upload Vendor Logo
# =========================================================

@router.post("/{vendor_id}/logo")
async def upload_vendor_logo(
    vendor_id: str,
    file: UploadFile = File(...),
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    validate_image(file.content_type)

    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    content = await file.read()
    variants = generate_variants(content)

    for size, data in variants.items():
        path = f"vendors/{vendor_id}/logo/{size}.jpg"
        upload_blob(path, data)

    # 🔥 SAVE BASE PATH ONLY
    vendor.logo_blob_path = f"vendors/{vendor_id}/logo"
    await engine.save(vendor)

    return success_response(
        message="Vendor logo uploaded successfully",
        data={"vendor_id": vendor_id},
    )


# =========================================================
# Upload Service Images
# =========================================================

@router.post("/{vendor_id}/services/{service_id}/images")
async def upload_service_images(
    vendor_id: str,
    service_id: str,
    files: List[UploadFile] = File(...),
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = await engine.find_one(
        VendorService,
        VendorService.id == ObjectId(service_id),
    )

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    new_blob_paths: List[str] = []

    for file in files:
        validate_image(file.content_type)

        blob_path = await upload_and_process_image(
            file=file,
            container="vendor-services",
            folder=f"vendors/{vendor_id}/services/{service_id}",
        )

        new_blob_paths.append(blob_path)

    # 🔥 PERSIST TO DB (THIS WAS THE CORE ISSUE)
    service.image_blob_paths.extend(new_blob_paths)
    await engine.save(service)

    return success_response(
        message="Service images uploaded successfully",
        data={
            "service_id": service_id,
            "image_count": len(service.image_blob_paths),
        },
    )
