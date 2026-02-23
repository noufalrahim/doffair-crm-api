from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from fastapi.responses import Response
import asyncio
import time
from typing import List
from core.security import get_current_token
from core.azure_client import upload_file_to_blob, delete_file_from_blob, download_file_from_blob
from vendor.schemas.media import ImageResponseSchema, MessageResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vendor/media",
    tags=["Vendor - Media"],
)

@router.post("/upload", response_model=ImageResponseSchema)
async def upload_images(
    image_type: str = Query(..., description="Type of image: profile_image, vaccination, message, groomer, kyc, invoice"),
    images: List[UploadFile] = File(...),
    token: dict = Depends(get_current_token)
):
    """
    Upload images directly to Azure Blob Storage asynchronously and in parallel.
    """
    valid_types = ["profile_image", "vaccination", "message", "groomer", "kyc", "invoice"]
    if image_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid image_type. Must be one of {valid_types}")

    vendor_id = token.get("vendor_id", "unknown")
    
    try:
        # Create a list to keep track of upload tasks
        upload_tasks = []

        # Add each file as a task to upload to blob storage
        for file in images:
            if file.content_type not in [
                'image/jpeg', 'image/png', 'image/jpg', 'image/gif', 
                'image/webp', 'image/tiff', 'image/bmp', 'image/heic', 
                'image/heif', 'image/svg+xml', 'application/pdf'
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{file.filename}' is not a valid image/document file"
                )
            # Reset pointer before starting task (just in case)
            await file.seek(0)
            upload_tasks.append(upload_file_to_blob(vendor_id, file, image_type))

        # Wait for all upload tasks to complete in parallel
        logger.info(f"Starting {len(upload_tasks)} image upload tasks asynchronously ...")
        start = time.perf_counter()
        image_paths = await asyncio.gather(*upload_tasks)
        logger.info(f"Completed {len(upload_tasks)} image upload tasks in {time.perf_counter() - start:.2f} seconds")

        return ImageResponseSchema(status='Images uploaded successfully!', paths=image_paths)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Could not upload images due to exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading to storage: {str(e)}")

@router.delete("/delete", response_model=MessageResponse)
async def delete_image(
    image_path: str = Query(..., description="Path of the image to delete"),
    token: dict = Depends(get_current_token)
):
    """
    Delete image from Azure Blob Storage asynchronously.
    """
    try:
        logger.info(f'Deleting image from "{image_path}" ...')
        await delete_file_from_blob(image_path)
        logger.info(f'Deleted image from "{image_path}"')
        return MessageResponse(status='Image deleted successfully!')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {image_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting from storage: {str(e)}")

@router.get("/view",
             summary='Download/View image',
             status_code=status.HTTP_200_OK,
             response_class=Response)
async def view_image(
    image_path: str = Query(..., description="Path of the image to view")
):
    """
    Download/View image from Azure Blob Storage.
    Note: Public endpoint for demonstration purposes. Use SAS URLs for production.
    """
    try:
        logger.info(f'Downloading image from "{image_path}" ...')
        image_bytes = await download_file_from_blob(image_path)
        
        # Determine media type
        media_type = "image/png"
        if image_path.lower().endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        elif image_path.lower().endswith(".gif"):
            media_type = "image/gif"
        elif image_path.lower().endswith(".webp"):
            media_type = "image/webp"
        elif image_path.lower().endswith(".pdf"):
            media_type = "application/pdf"
            
        return Response(image_bytes, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Could not download image {image_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")
