from odmantic import Model, Field, EmbeddedModel
from datetime import datetime
from typing import Optional, List

class PrescriptionMedication(EmbeddedModel):
    """
    Medication details within a prescription
    """
    name: str
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    timing: str = ""  # e.g. "After Food", "Before Food"
    qty: str = ""  # e.g. "56", "28"
    notes: str = ""

class PrescriptionData(Model):
    """
    Structured prescription document
    """
    vendor_id: str
    booking_id: str
    
    # Patient/Owner details
    pet_name: str = ""
    pet_id: str = ""
    owner_name: str = ""
    owner_id: str = ""
    
    # Medical details
    complaints: str = ""
    medical_history: str = ""
    drug_allergies: str = ""
    tests_prescribed: str = ""
    diagnosis: str
    medications: List[PrescriptionMedication]
    instructions: str = ""
    follow_up_date: Optional[datetime] = None
    
    # Clinic/Doctor context
    clinic_name: str = ""
    doctor_name: str = ""
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "prescriptions_data",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["booking_id"]},
            {"fields": ["pet_id"]},
            {"fields": ["owner_id"]},
            {"fields": ["is_active"]},
        ],
    }
