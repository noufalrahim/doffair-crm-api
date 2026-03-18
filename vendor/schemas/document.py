from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    is_verified: Optional[bool] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None

class DocumentResponse(BaseModel):
    id: str
    vendor_id: str
    name: str
    link: str
    type: str
    description: Optional[str] = None
    is_verified: bool
    message: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "name": "KYC Document",
                "link": "https://storage.example.com/vendor/kyc.pdf",
                "type": "kyc",
                "description": "Vendor identification document",
                "is_verified": False,
                "message": "Verification pending",
                "is_active": True,
                "created_at": "2024-03-11T10:00:00Z",
                "updated_at": "2024-03-11T10:00:00Z"
            }
        }

class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]
