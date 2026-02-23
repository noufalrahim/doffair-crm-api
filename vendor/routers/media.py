from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, Request
from typing import List, Optional
import aiohttp
from core.config import settings
from core.security import get_current_token
from utils.response import success_response, error_response

router = APIRouter(
    prefix="/vendor/media",
    tags=["Vendor - Media"],
)

@router.post("/upload")
async def upload_image(
    request: Request,
    image_type: str = Query(..., description="Type of image: profile_image, vaccination, message, groomer, kyc, invoice"),
    images: List[UploadFile] = File(...),
    token: dict = Depends(get_current_token)
):
    """
    Proxy to upload images to the image service.
    """
    valid_types = ["profile_image", "vaccination", "message", "groomer", "kyc", "invoice"]
    if image_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid image_type. Must be one of {valid_types}")

    url = f"{settings.IMAGE_BASE_URL}/image?image_type={image_type}"
    
    # Extract Authorization header from current request
    auth_header = request.headers.get("Authorization")
    headers = {
        "accept": "application/json",
        "Authorization": auth_header
    }

    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        for image in images:
            content = await image.read()
            data.add_field('images', content, filename=image.filename, content_type=image.content_type)
        
        try:
            async with session.post(url, headers=headers, data=data) as response:
                result = await response.json()
                if response.status >= 400:
                    return error_response(message=result.get("detail", "Failed to upload image")).model_dump()
                return success_response(data=result, message="Image(s) uploaded successfully").model_dump()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to image service: {str(e)}")

@router.delete("/delete")
async def delete_image(
    request: Request,
    image_path: str = Query(..., description="Path of the image to delete"),
    token: dict = Depends(get_current_token)
):
    """
    Proxy to delete images from the image service.
    """
    url = f"{settings.IMAGE_BASE_URL}/image?image_path={image_path}"
    
    # Extract Authorization header from current request
    auth_header = request.headers.get("Authorization")
    headers = {
        "accept": "application/json",
        "Authorization": auth_header
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=headers) as response:
                result = await response.json()
                if response.status >= 400:
                    return error_response(message=result.get("detail", "Failed to delete image")).model_dump()
                return success_response(data=result, message="Image deleted successfully").model_dump()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to image service: {str(e)}")
