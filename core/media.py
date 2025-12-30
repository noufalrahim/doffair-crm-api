from typing import Optional, List
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
import uuid

from core.storage import upload_blob, generate_signed_url


# ---------------------------------------------------------
# Image config
# ---------------------------------------------------------

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# ---------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------

def _resize_image(image: Image.Image, max_size: int) -> bytes:
    img = image.copy()
    img.thumbnail((max_size, max_size))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------
# 🔥 UPLOAD PIPELINE (THIS WAS MISSING)
# ---------------------------------------------------------

async def upload_and_process_image(
    *,
    file: UploadFile,
    container: str,
    folder: str,
) -> str:
    """
    Validates, compresses, uploads image variants to blob storage.

    Returns:
        base_blob_path (str)
        Example: vendors/{vendor_id}/services/{service_id}/{image_id}
    """

    # Validate type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type",
        )

    raw = await file.read()

    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    image_id = uuid.uuid4().hex
    base_path = f"{folder}/{image_id}"

    variants = {
        "original": _resize_image(image, 1600),
        "medium": _resize_image(image, 800),
        "thumbnail": _resize_image(image, 300),
    }

    for variant, content in variants.items():
        blob_path = f"{base_path}_{variant}.jpg"
        upload_blob(blob_path, content)

    # 🔥 ONLY BASE PATH IS STORED IN DB
    return base_path


# ---------------------------------------------------------
# READ PIPELINE (SIGNED URL GENERATION)
# ---------------------------------------------------------

def build_image_set(blob_base_path: Optional[str]) -> Optional[dict]:
    if not blob_base_path:
        return None

    return {
        "original": generate_signed_url(f"{blob_base_path}_original.jpg"),
        "medium": generate_signed_url(f"{blob_base_path}_medium.jpg"),
        "thumbnail": generate_signed_url(f"{blob_base_path}_thumbnail.jpg"),
    }


def build_image_list(blob_base_paths: List[str]) -> List[dict]:
    return [
        image_set
        for p in blob_base_paths
        if (image_set := build_image_set(p)) is not None
    ]
