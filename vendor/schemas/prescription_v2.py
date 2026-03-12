"""
Prescription schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PrescriptionUploadRequest(BaseModel):
    """Request schema for uploading prescription (form data)"""
    booking_id: str = Field(..., description="Booking ID to link prescription to")
    notes: Optional[str] = Field(None, description="Optional notes about prescription")
    prescription_date: Optional[datetime] = Field(None, description="Date of prescription (defaults to now)")


class PrescriptionResponse(BaseModel):
    """Response schema for prescription data"""
    id: str
    vendor_id: str
    customer_id: str
    booking_id: str
    
    file_name: str
    file_type: str
    file_size: int
    
    blob_url: str
    blob_path: str
    cdn_url: str  # Empty string if not set
    
    notes: str  # Empty string if not set
    prescription_date: datetime
    uploaded_at: datetime
    is_active: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "69830c42b18ec9ac59765093",
                "vendor_id": "69804efc422c93604361e316",
                "customer_id": "offline_9876543210",
                "booking_id": "69830c42b18ec9ac59765094",
                "file_name": "blood_test_report.pdf",
                "file_type": "application/pdf",
                "file_size": 245678,
                "blob_url": "https://storage.azure.com/prescriptions/...",
                "blob_path": "prescriptions/vendor_id/booking_id/uuid.pdf",
                "cdn_url": "https://cdn.example.com/prescriptions/...",
                "notes": "Blood test results - all normal",
                "prescription_date": "2026-02-04T10:00:00",
                "uploaded_at": "2026-02-04T10:15:00",
                "is_active": True
            }
        }


class PrescriptionListResponse(BaseModel):
    """Response schema for list of prescriptions"""
    total: int
    prescriptions: list[PrescriptionResponse]


from vendor.schemas.prescription_data import PrescriptionDataResponse

class PrescriptionDownloadUrlResponse(BaseModel):
    """Response schema for prescription download URL"""
    prescription_id: str
    download_url: str
    expires_in_hours: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "prescription_id": "69830c42b18ec9ac59765093",
                "download_url": "https://storage.azure.com/prescriptions/...?sas_token=...",
                "expires_in_hours": 24
            }
        }

class UnifiedPrescriptionResponse(BaseModel):
    """Unified response containing both uploaded documents and structured medication data"""
    booking_id: str
    uploaded_files: list[PrescriptionResponse]
    structured_data: list[PrescriptionDataResponse]
