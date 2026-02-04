"""
Prescription management endpoints
Upload, view, and manage prescription files for bookings
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from odmantic import AIOEngine
from typing import Optional
from datetime import datetime

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response, error_response
from vendor.services.prescription_service_v2 import (
    upload_prescription,
    get_prescription_by_id,
    list_prescriptions_by_booking,
    list_prescriptions_by_customer_phone,
    delete_prescription,
    get_prescription_download_url
)
from vendor.schemas.prescription_v2 import (
    PrescriptionResponse,
    PrescriptionListResponse,
    PrescriptionDownloadUrlResponse
)

router = APIRouter(
    prefix="/vendor/prescriptions",
    tags=["Vendor - Prescriptions"]
)


@router.post("/upload", response_model=dict)
async def upload_prescription_endpoint(
    file: UploadFile = File(..., description="Prescription file (image or PDF, max 10MB)"),
    booking_id: str = Form(..., description="Booking ID to link prescription to"),
    notes: Optional[str] = Form(None, description="Optional notes about prescription"),
    prescription_date: Optional[str] = Form(None, description="Date of prescription (ISO format, defaults to now)"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Upload a prescription file for a booking
    
    - **file**: Image (JPG, PNG, GIF, WEBP) or PDF file (max 10MB)
    - **booking_id**: ID of the booking this prescription belongs to
    - **notes**: Optional notes about the prescription
    - **prescription_date**: Date of prescription (ISO format like "2026-02-04T10:00:00")
    
    Returns uploaded prescription details with Azure Blob Storage URL
    """
    vendor_id = current_vendor["vendor_id"]
    
    # Parse prescription_date if provided
    parsed_date = None
    if prescription_date:
        try:
            parsed_date = datetime.fromisoformat(prescription_date.replace('Z', '+00:00'))
        except ValueError:
            return error_response(
                message=f"Invalid prescription_date format. Use ISO format like '2026-02-04T10:00:00'"
            ).model_dump()
    
    prescription = await upload_prescription(
        engine=engine,
        vendor_id=vendor_id,
        booking_id=booking_id,
        file=file,
        notes=notes,
        prescription_date=parsed_date
    )
    
    response_data = PrescriptionResponse(
        id=str(prescription.id),
        vendor_id=prescription.vendor_id,
        customer_id=prescription.customer_id,
        booking_id=prescription.booking_id,
        file_name=prescription.file_name,
        file_type=prescription.file_type,
        file_size=prescription.file_size,
        blob_url=prescription.blob_url,
        blob_path=prescription.blob_path,
        cdn_url=prescription.cdn_url,
        notes=prescription.notes,
        prescription_date=prescription.prescription_date,
        uploaded_at=prescription.uploaded_at,
        is_active=prescription.is_active
    )
    
    return success_response(
        message="Prescription uploaded successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.get("/{prescription_id}", response_model=dict)
async def get_prescription_endpoint(
    prescription_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get prescription details by ID
    
    Returns prescription metadata and file URL
    """
    vendor_id = current_vendor["vendor_id"]
    
    prescription = await get_prescription_by_id(
        engine=engine,
        vendor_id=vendor_id,
        prescription_id=prescription_id
    )
    
    response_data = PrescriptionResponse(
        id=str(prescription.id),
        vendor_id=prescription.vendor_id,
        customer_id=prescription.customer_id,
        booking_id=prescription.booking_id,
        file_name=prescription.file_name,
        file_type=prescription.file_type,
        file_size=prescription.file_size,
        blob_url=prescription.blob_url,
        blob_path=prescription.blob_path,
        cdn_url=prescription.cdn_url,
        notes=prescription.notes,
        prescription_date=prescription.prescription_date,
        uploaded_at=prescription.uploaded_at,
        is_active=prescription.is_active
    )
    
    return success_response(
        message="Prescription retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.get("/{prescription_id}/download-url", response_model=dict)
async def get_prescription_download_url_endpoint(
    prescription_id: str,
    expiry_hours: int = Query(24, ge=1, le=168, description="Hours until URL expires (1-168)"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get temporary download URL for prescription file
    
    Returns a signed URL that expires after specified hours (default: 24h, max: 7 days)
    """
    vendor_id = current_vendor["vendor_id"]
    
    download_url = await get_prescription_download_url(
        engine=engine,
        vendor_id=vendor_id,
        prescription_id=prescription_id,
        expiry_hours=expiry_hours
    )
    
    response_data = PrescriptionDownloadUrlResponse(
        prescription_id=prescription_id,
        download_url=download_url,
        expires_in_hours=expiry_hours
    )
    
    return success_response(
        message="Download URL generated successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.get("", response_model=dict)
async def list_prescriptions_endpoint(
    booking_id: Optional[str] = Query(None, description="Filter by booking ID"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List prescriptions with optional filters
    
    - **No filters**: Returns empty list (must provide either booking_id or customer_phone)
    - **booking_id**: Get all prescriptions for a specific booking
    - **customer_phone**: Get all prescriptions for a customer across all bookings
    """
    vendor_id = current_vendor["vendor_id"]
    
    if not booking_id and not customer_phone:
        return error_response(
            message="Please provide either booking_id or customer_phone parameter"
        ).model_dump()
    
    # Get prescriptions based on filter
    if booking_id:
        prescriptions = await list_prescriptions_by_booking(
            engine=engine,
            vendor_id=vendor_id,
            booking_id=booking_id
        )
    else:  # customer_phone
        prescriptions = await list_prescriptions_by_customer_phone(
            engine=engine,
            vendor_id=vendor_id,
            customer_phone=customer_phone
        )
    
    # Convert to response format
    prescription_responses = [
        PrescriptionResponse(
            id=str(p.id),
            vendor_id=p.vendor_id,
            customer_id=p.customer_id,
            booking_id=p.booking_id,
            file_name=p.file_name,
            file_type=p.file_type,
            file_size=p.file_size,
            blob_url=p.blob_url,
            blob_path=p.blob_path,
            cdn_url=p.cdn_url,
            notes=p.notes,
            prescription_date=p.prescription_date,
            uploaded_at=p.uploaded_at,
            is_active=p.is_active
        ).model_dump()
        for p in prescriptions
    ]
    
    response_data = PrescriptionListResponse(
        total=len(prescription_responses),
        prescriptions=prescription_responses
    )
    
    return success_response(
        message="Prescriptions retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.delete("/{prescription_id}", response_model=dict)
async def delete_prescription_endpoint(
    prescription_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Delete a prescription (soft delete - marks as inactive)
    
    File remains in Azure Blob Storage but prescription is hidden from queries
    """
    vendor_id = current_vendor["vendor_id"]
    
    await delete_prescription(
        engine=engine,
        vendor_id=vendor_id,
        prescription_id=prescription_id
    )
    
    return success_response(
        message="Prescription deleted successfully",
        data={"prescription_id": prescription_id, "deleted": True}
    ).model_dump()
