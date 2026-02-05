"""
Pet Image Upload - Azure Blob Storage
Allows users to upload pet images when creating bookings
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_user
from core.azure_blob import azure_blob_service
from utils.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pet-images",
    tags=["Pet Images"],
)


@router.post("/upload")
async def upload_pet_image(
    file: UploadFile = File(...),
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Upload a pet image to Azure Blob Storage
    
    Returns the blob URL to be included in booking creation
    
    **Allowed formats**: JPG, JPEG, PNG, WEBP
    **Max size**: 10MB
    """
    user_id = token.get("user_id")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        return error_response(
            message=f"Invalid file type. Allowed: JPG, PNG, WEBP. Got: {file.content_type}"
        ).model_dump()
    
    # Validate file size (10MB max)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        return error_response(
            message=f"File too large. Max size: 10MB. Your file: {file_size / (1024*1024):.2f}MB"
        ).model_dump()
    
    try:
        # Upload to Azure Blob Storage
        # Path structure: pet-images/{user_id}/
        folder_path = f"pet-images/{user_id}"
        
        upload_result = azure_blob_service.upload_file(
            file_data=file.file,
            file_name=file.filename,
            folder_path=folder_path,
            content_type=file.content_type
        )
        
        logger.info(f"🐾 Pet image uploaded: {upload_result['blob_path']} by user {user_id}")
        
        return success_response(
            message="Pet image uploaded successfully",
            data={
                "image_url": upload_result["blob_url"],
                "blob_path": upload_result["blob_path"],
                "file_name": upload_result["file_name"],
                "file_size": upload_result["file_size"],
                "cdn_url": upload_result.get("cdn_url")
            }
        ).model_dump()
        
    except Exception as e:
        logger.error(f"❌ Failed to upload pet image: {str(e)}")
        return error_response(
            message=f"Failed to upload image: {str(e)}"
        ).model_dump()


@router.delete("/{blob_path:path}")
async def delete_pet_image(
    blob_path: str,
    token: dict = Depends(require_user),
):
    """
    Delete a pet image from Azure Blob Storage
    
    User can only delete their own images (path must start with pet-images/{user_id}/)
    """
    user_id = token.get("user_id")
    
    # Security check: ensure user can only delete their own images
    expected_prefix = f"pet-images/{user_id}/"
    if not blob_path.startswith(expected_prefix):
        return error_response(
            message="Access denied. You can only delete your own pet images."
        ).model_dump()
    
    try:
        success = azure_blob_service.delete_file(blob_path)
        
        if success:
            return success_response(
                message="Pet image deleted successfully",
                data={"blob_path": blob_path}
            ).model_dump()
        else:
            return error_response(
                message="Failed to delete image"
            ).model_dump()
            
    except Exception as e:
        logger.error(f"❌ Failed to delete pet image: {str(e)}")
        return error_response(
            message=f"Failed to delete image: {str(e)}"
        ).model_dump()
