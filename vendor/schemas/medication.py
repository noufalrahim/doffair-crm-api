from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MedicationCreate(BaseModel):
    name: str = Field(..., description="Name of the medication")
    dosage: str = Field(..., description="Dosage (e.g., 500mg, 5ml)")
    frequency: str = Field(..., description="Frequency (e.g., Once a day, Twice a day)")
    duration: str = Field(..., description="Duration (e.g., 5 days, 1 week)")
    notes: Optional[str] = Field("", description="Optional notes about the medication")

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class MedicationResponse(BaseModel):
    id: str
    vendor_id: str
    name: str = Field(..., example="Amoxicillin")
    dosage: str = Field(..., example="500mg")
    frequency: str = Field(..., example="Twice a day")
    duration: str = Field(..., example="7 days")
    notes: str = Field(..., example="Take after meals")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "Twice a day",
                "duration": "7 days",
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
                        "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                        "name": "Amoxicillin",
                        "dosage": "500mg",
                        "frequency": "Twice a day",
                        "duration": "7 days",
                        "notes": "Take after meals",
                        "is_active": True,
                        "created_at": "2024-03-11T10:00:00Z",
                        "updated_at": "2024-03-11T10:00:00Z"
                    }
                ]
            }
        }
