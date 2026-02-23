"""
Prescription service - Upload and manage prescription files
Uses Azure Blob Storage for file storage
Links prescriptions to bookings
"""
from datetime import datetime
from typing import Optional, List
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status, UploadFile
import logging

from vendor.models.prescription import Prescription
from user.models.booking import Booking
from core.azure_client import upload_file_to_blob, generate_blob_sas_url, blob_service_client
from core.config import settings

logger = logging.getLogger(__name__)


ALLOWED_FILE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
    "application/pdf"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def upload_prescription(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str,
    file: UploadFile,
    notes: Optional[str] = None,
    prescription_date: Optional[datetime] = None
) -> Prescription:
    """
    Upload a prescription file for a booking
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        booking_id: Booking ID to link prescription to
        file: Uploaded file (image or PDF)
        notes: Optional notes about prescription
        prescription_date: Date of prescription (defaults to now)
    
    Returns:
        Created Prescription document
    
    Raises:
        HTTPException: If booking not found, invalid file type, or file too large
    """
    # Validate booking exists and belongs to vendor
    try:
        booking = await engine.find_one(
            Booking,
            (Booking.id == ObjectId(booking_id)) & 
            (Booking.vendor_id == vendor_id)
        )
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found or does not belong to vendor"
            )
    except Exception as e:
        logger.error(f"Error finding booking {booking_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid booking ID: {booking_id}"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: images (jpg, png, gif, webp) and PDF. Got: {file.content_type}"
        )
    
    # Read file and check size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Reset file pointer for upload
    await file.seek(0)
    try:
        # Path structure: prescriptions/{vendor_id}/{booking_id}/
        # In the new client, upload_file_to_blob expects user_id, file, image_type
        # and it constructs path as {user_id}/{image_type}/{uuid}{ext}
        
        blob_path = await upload_file_to_blob(
            user_id=vendor_id,
            upload_file=file,
            image_type=f"prescriptions/{booking_id}"
        )
        
        blob_url = f"{blob_service_client.primary_endpoint}{settings.AZURE_BLOB_CONTAINER}/{blob_path}"
        cdn_url = f"{settings.AZURE_CDN_BASE_URL}/{blob_path}" if settings.AZURE_CDN_BASE_URL else ""
        
        logger.info(f"📄 File uploaded to Azure: {blob_path}")
        
        # Extract customer phone from booking
        customer_phone = booking.user_phone
        
        # Create prescription document
        prescription = Prescription(
            vendor_id=vendor_id,
            customer_id=booking.user_id,
            booking_id=booking_id,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            blob_url=blob_url,
            blob_path=blob_path,
            cdn_url=cdn_url,
            notes=notes or "",
            prescription_date=prescription_date or datetime.utcnow(),
            uploaded_at=datetime.utcnow(),
            is_active=True
        )
        
        await engine.save(prescription)
        logger.info(f"✅ Prescription created: {prescription.id} for booking {booking_id}")
        
        return prescription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload prescription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload prescription: {str(e)}"
        )


async def get_prescription_by_id(
    engine: AIOEngine,
    vendor_id: str,
    prescription_id: str
) -> Prescription:
    """
    Get prescription by ID
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        prescription_id: Prescription ID
    
    Returns:
        Prescription document
    
    Raises:
        HTTPException: If prescription not found
    """
    try:
        prescription = await engine.find_one(
            Prescription,
            (Prescription.id == ObjectId(prescription_id)) & 
            (Prescription.vendor_id == vendor_id) &
            (Prescription.is_active == True)
        )
        
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription {prescription_id} not found"
            )
        
        return prescription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prescription {prescription_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid prescription ID: {prescription_id}"
        )


async def list_prescriptions_by_booking(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str
) -> List[Prescription]:
    """
    Get all prescriptions for a specific booking
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        booking_id: Booking ID
    
    Returns:
        List of prescriptions
    """
    prescriptions = await engine.find(
        Prescription,
        (Prescription.vendor_id == vendor_id) & 
        (Prescription.booking_id == booking_id) &
        (Prescription.is_active == True)
    )
    
    return list(prescriptions)


async def list_prescriptions_by_customer_phone(
    engine: AIOEngine,
    vendor_id: str,
    customer_phone: str
) -> List[Prescription]:
    """
    Get all prescriptions for a customer by phone number
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        customer_phone: Customer phone number
    
    Returns:
        List of prescriptions sorted by upload date (newest first)
    """
    # First find all bookings for this customer phone
    bookings = await engine.find(
        Booking,
        (Booking.vendor_id == vendor_id) & 
        (Booking.user_phone == customer_phone)
    )
    
    booking_ids = [str(b.id) for b in bookings]
    
    if not booking_ids:
        return []
    
    # Get all prescriptions for these bookings
    # Filter by vendor_id and booking_id in list (only non-empty)
    prescriptions = await engine.find(
        Prescription,
        (Prescription.vendor_id == vendor_id) & 
        (Prescription.booking_id.in_(booking_ids)) &
        (Prescription.booking_id != "") &
        (Prescription.is_active == True),
        sort=Prescription.uploaded_at.desc()
    )
    
    return list(prescriptions)


async def delete_prescription(
    engine: AIOEngine,
    vendor_id: str,
    prescription_id: str
) -> bool:
    """
    Soft delete a prescription (mark as inactive)
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        prescription_id: Prescription ID
    
    Returns:
        True if deleted successfully
    
    Raises:
        HTTPException: If prescription not found
    """
    prescription = await get_prescription_by_id(engine, vendor_id, prescription_id)
    
    prescription.is_active = False
    await engine.save(prescription)
    
    logger.info(f"🗑️ Prescription {prescription_id} marked as deleted")
    
    return True


async def get_prescription_download_url(
    engine: AIOEngine,
    vendor_id: str,
    prescription_id: str,
    expiry_hours: int = 24
) -> str:
    """
    Get temporary signed URL for prescription download
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        prescription_id: Prescription ID
        expiry_hours: Hours until URL expires (default: 24)
    
    Returns:
        Signed URL with SAS token
    
    Raises:
        HTTPException: If prescription not found
    """
    prescription = await get_prescription_by_id(engine, vendor_id, prescription_id)
    
    try:
        signed_url = generate_blob_sas_url(
            blob_path=prescription.blob_path,
            expiry_hours=expiry_hours
        )
        return signed_url
    except Exception as e:
        logger.error(f"❌ Failed to generate download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )
