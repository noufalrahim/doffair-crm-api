from odmantic import Model, Field
from datetime import datetime
from typing import Optional

class Medication(Model):
    """
    Medication master record managed by vendor
    """
    vendor_id: str
    name: str
    dosage: str
    frequency: str
    duration: str
    notes: str = ""
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "medications",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vendor_id", "name"]},
            {"fields": ["is_active"]},
        ],
    }
