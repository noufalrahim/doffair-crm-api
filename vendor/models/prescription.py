"""
Prescription model for storing customer prescription files
Supports images and PDFs stored in Azure Blob Storage
"""
from datetime import datetime
from odmantic import Model, Field
from typing import Optional
from bson import ObjectId


class Prescription(Model):
    """
    Prescription document linked to customer and booking
    Stores file metadata and Azure Blob Storage references
    """
    # Relationships
    vendor_id: str
    customer_id: str
    
    # File Information
    file_name: str
    file_type: str
    file_size: int
    
    # Azure Blob Storage
    blob_url: str
    blob_path: str
    
    # Metadata
    is_active: bool = True
    
    # STRING FIELDS - Use empty string defaults instead of Optional[str] for ODMantic 1.0.0 bug
    booking_id: str = ""
    cdn_url: str = ""
    notes: str = ""
    
    # DATETIME FIELDS - At the end
    prescription_date: Optional[datetime] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "prescriptions",
        "indexes": [
            # Primary lookups
            {"fields": ["customer_id"]},
            {"fields": ["vendor_id"]},
            {"fields": ["booking_id"]},
            
            # Common queries
            {"fields": ["vendor_id", "customer_id"]},
            {"fields": ["customer_id", "uploaded_at"]},
            {"fields": ["vendor_id", "is_active"]},
            
            # Timeline queries
            {"fields": ["uploaded_at"]},
        ],
    }
