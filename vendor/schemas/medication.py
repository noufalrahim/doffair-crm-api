from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MedicationCreate(BaseModel):
    name: str = Field(..., description="Name of the medication")
    vertical_id: str = Field(..., description="ID of the vertical (e.g., pharmacy)")
    vendor_id: Optional[str] = Field(None, description="Optional ID of the vendor")
    description: Optional[str] = Field(None, description="Optional description of the medication")
    category: str = Field(..., description="Category of the medicine")
    quantity_to_give: str = Field(..., description="Quantity to give (e.g., 1 strip, 1 bottle)")
    stock_quantity: int = Field(..., description="Current stock quantity")
    unit: str = Field(..., description="Unit of measurement (e.g., tablets, ml)")
    base_price: float = Field(..., description="Base price of the medication")
    batch_id: str = Field(..., description="Batch identifier")
    manufacturer: str = Field(..., description="Manufacturer name")
    mfd_date: str = Field(..., description="Manufacturing date")
    expiry_date: str = Field(..., description="Expiry date")
    images: Optional[list[str]] = Field(None, description="Optional list of image URLs")
    
    dosage: Optional[str] = Field(None, description="Dosage (e.g., 500mg, 5ml)")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., Once a day, Twice a day)")
    duration: Optional[str] = Field(None, description="Duration (e.g., 5 days, 1 week)")
    notes: Optional[str] = Field("", description="Optional notes about the medication")

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    vertical_id: Optional[str] = None
    vendor_id: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity_to_give: Optional[str] = None
    stock_quantity: Optional[int] = None
    unit: Optional[str] = None
    base_price: Optional[float] = None
    batch_id: Optional[str] = None
    manufacturer: Optional[str] = None
    mfd_date: Optional[str] = None
    expiry_date: Optional[str] = None
    images: Optional[list[str]] = None
    
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class MedicationResponse(BaseModel):
    id: str
    vertical_id: str
    vendor_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: str
    quantity_to_give: str
    stock_quantity: int
    unit: str
    base_price: float
    batch_id: str
    manufacturer: str
    mfd_date: str
    expiry_date: str
    images: Optional[list[str]] = None
    
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "vertical_id": "pharmacy_vertical_id",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "name": "Paracetamol",
                "description": "Pain reliever and fever reducer",
                "category": "Analgesics",
                "quantity_to_give": "1 strip",
                "stock_quantity": 100,
                "unit": "tablets",
                "base_price": 50.0,
                "batch_id": "BAT12345",
                "manufacturer": "HealthCorp",
                "mfd_date": "2024-01-01",
                "expiry_date": "2026-01-01",
                "images": ["https://example.com/image.jpg"],
                "dosage": "500mg",
                "frequency": "Three times a day",
                "duration": "5 days",
                "notes": "Take after meals",
                "is_active": True,
                "created_at": "2024-03-11T10:00:00Z",
                "updated_at": "2024-03-11T10:00:00Z"
            }
        }

class MedicationListResponse(BaseModel):
    total: int
    medications: list[MedicationResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "medications": [
                    {
                        "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                        "vertical_id": "pharmacy_vertical_id",
                        "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                        "name": "Paracetamol",
                        "category": "Analgesics",
                        "quantity_to_give": "1 strip",
                        "stock_quantity": 100,
                        "unit": "tablets",
                        "base_price": 50.0,
                        "batch_id": "BAT12345",
                        "manufacturer": "HealthCorp",
                        "mfd_date": "2024-01-01",
                        "expiry_date": "2026-01-01",
                        "is_active": True,
                        "created_at": "2024-03-11T10:00:00Z",
                        "updated_at": "2024-03-11T10:00:00Z"
                    }
                ]
            }
        }
