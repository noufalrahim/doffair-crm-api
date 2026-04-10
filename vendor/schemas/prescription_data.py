from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PrescriptionMedicationSchema(BaseModel):
    name: str = Field(..., description="Name of the medication")
    dosage: str = Field("", description="Dosage (e.g., 500mg, 5ml)")
    frequency: str = Field("", description="Frequency (e.g., Once a day, Twice a day)")
    duration: str = Field("", description="Duration (e.g., 5 days, 1 week)")
    timing: str = Field("", description="Timing (e.g., After Food, Before Food)")
    qty: str = Field("", description="Quantity (e.g., 56, 28)")
    notes: str = Field("", description="Optional notes about the medication")

class PrescriptionDataCreate(BaseModel):
    booking_id: str = Field(..., description="ID of the booking")
    pet_name: Optional[str] = Field("", description="Name of the pet")
    pet_id: Optional[str] = Field("", description="ID of the pet")
    owner_name: Optional[str] = Field("", description="Name of the owner")
    owner_id: Optional[str] = Field("", description="ID of the owner")
    complaints: Optional[str] = Field("", description="Patient complaints")
    medical_history: Optional[str] = Field("", description="Medical history")
    drug_allergies: Optional[str] = Field("", description="Drug allergies")
    tests_prescribed: Optional[str] = Field("", description="Tests prescribed")
    diagnosis: str = Field(..., description="Diagnosis results")
    medications: List[PrescriptionMedicationSchema] = Field(..., description="List of medications")
    instructions: Optional[str] = Field("", description="General instructions")
    follow_up_date: Optional[datetime] = Field(None, description="Optional follow-up date")
    clinic_name: Optional[str] = Field("", description="Clinic/Location name")
    doctor_name: Optional[str] = Field("", description="Doctor name")

class PrescriptionDataUpdate(BaseModel):
    pet_name: Optional[str] = None
    pet_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_id: Optional[str] = None
    complaints: Optional[str] = None
    medical_history: Optional[str] = None
    drug_allergies: Optional[str] = None
    tests_prescribed: Optional[str] = None
    diagnosis: Optional[str] = None
    medications: Optional[List[PrescriptionMedicationSchema]] = None
    instructions: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    clinic_name: Optional[str] = None
    doctor_name: Optional[str] = None
    is_active: Optional[bool] = None

class PrescriptionDataResponse(BaseModel):
    id: str
    vendor_id: str
    booking_id: str = Field(..., example="65f1a2b3c4d5e6f7a8b9c0d3")
    pet_name: str = Field(..., example="Buddy")
    pet_id: str = Field(..., example="pet_123")
    owner_name: str = Field(..., example="John Doe")
    owner_id: str = Field(..., example="owner_456")
    complaints: str = Field("", example="Vomiting and lethargy")
    medical_history: str = Field("", example="Previously treated for worms")
    drug_allergies: str = Field("", example="NIL")
    tests_prescribed: str = Field("", example="CBC, Blood Sugar")
    diagnosis: str = Field(..., example="Bacterial infection")
    medications: List[PrescriptionMedicationSchema]
    instructions: str = Field(..., example="Keep hydrated and monitor temperature")
    follow_up_date: Optional[datetime] = Field(None, example="2024-03-20T10:00:00Z")
    clinic_name: str = Field("", example="Pets World - Himathnagar")
    doctor_name: str = Field("", example="Dr. Smith")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d4",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "booking_id": "65f1a2b3c4d5e6f7a8b9c0d3",
                "pet_name": "Buddy",
                "pet_id": "pet_123",
                "owner_name": "John Doe",
                "owner_id": "owner_456",
                "diagnosis": "Bacterial infection",
                "medications": [
                    {
                        "name": "Amoxicillin",
                        "dosage": "500mg",
                        "frequency": "Twice a day",
                        "duration": "7 days",
                        "notes": "Take after meals"
                    }
                ],
                "instructions": "Keep hydrated and monitor temperature",
                "follow_up_date": "2024-03-20T10:00:00Z",
                "is_active": True,
                "created_at": "2024-03-11T10:00:00Z",
                "updated_at": "2024-03-11T10:00:00Z"
            }
        }

class PrescriptionDataListResponse(BaseModel):
    total: int
    prescriptions: List[PrescriptionDataResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "prescriptions": [
                    {
                        "id": "65f1a2b3c4d5e6f7a8b9c0d4",
                        "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                        "booking_id": "65f1a2b3c4d5e6f7a8b9c0d3",
                        "pet_name": "Buddy",
                        "pet_id": "pet_123",
                        "owner_name": "John Doe",
                        "owner_id": "owner_456",
                        "diagnosis": "Bacterial infection",
                        "medications": [
                            {
                                "name": "Amoxicillin",
                                "dosage": "500mg",
                                "frequency": "Twice a day",
                                "duration": "7 days",
                                "notes": "Take after meals"
                            }
                        ],
                        "instructions": "Keep hydrated and monitor temperature",
                        "follow_up_date": "2024-03-20T10:00:00Z",
                        "is_active": True,
                        "created_at": "2024-03-11T10:00:00Z",
                        "updated_at": "2024-03-11T10:00:00Z"
                    }
                ]
            }
        }
