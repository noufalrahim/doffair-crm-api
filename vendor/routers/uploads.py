from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List

from core.security import require_vendor
from core.azure_blob import azure_blob_service
from utils.response import success_response

router = APIRouter(
    prefix="/vendor/uploads",
    tags=["Vendor - Uploads"],
)


@router.post("", response_model=dict)
async def upload_file(
    folder: str = Form(..., description="Folder/category to store the file in (e.g. 'logos', 'documents', 'pet-images')"),
    file: UploadFile = File(..., description="File to upload (max 10MB)"),
    token: dict = Depends(require_vendor()),
):
    """
    Common upload endpoint.
    
    Accepts a file and a `folder` key. The file is stored under:
      `{folder}/{vendor_id}/{unique_filename}`
    
    Returns the CDN URL (or blob URL as fallback).
    """
    vendor_id = token.get("vendor_id")

    # Validate file size (10MB limit)
    contents = await file.read()
    max_size = 10 * 1024 * 1024  # 10 MB
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Reset for upload
    import io
    file_data = io.BytesIO(contents)

    folder_path = f"{folder}/{vendor_id}"

    result = azure_blob_service.upload_file(
        file_data=file_data,
        file_name=file.filename or "upload",
        folder_path=folder_path,
        content_type=file.content_type or "application/octet-stream",
    )

    url = result.get("cdn_url") or result.get("blob_url")

    return success_response(
        message="File uploaded successfully",
        data={
            "url": url,
            "blob_path": result["blob_path"],
            "file_name": result["file_name"],
            "file_size": result["file_size"],
        },
    ).model_dump()


@router.post("/multiple", response_model=dict)
async def upload_multiple_files(
    folder: str = Form(..., description="Folder/category to store files in"),
    files: List[UploadFile] = File(..., description="Files to upload (max 10MB each)"),
    token: dict = Depends(require_vendor()),
):
    """
    Upload multiple files at once.
    
    Each file is stored under:
      `{folder}/{vendor_id}/{unique_filename}`
    
    Returns a list of URLs.
    """
    vendor_id = token.get("vendor_id")
    max_size = 10 * 1024 * 1024
    folder_path = f"{folder}/{vendor_id}"

    import io
    uploaded = []

    for file in files:
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds 10MB limit",
            )

        file_data = io.BytesIO(contents)
        result = azure_blob_service.upload_file(
            file_data=file_data,
            file_name=file.filename or "upload",
            folder_path=folder_path,
            content_type=file.content_type or "application/octet-stream",
        )

        url = result.get("cdn_url") or result.get("blob_url")
        uploaded.append({
            "url": url,
            "blob_path": result["blob_path"],
            "file_name": result["file_name"],
            "file_size": result["file_size"],
        })

    return success_response(
        message=f"{len(uploaded)} file(s) uploaded successfully",
        data=uploaded,
    ).model_dump()
