from datetime import datetime
from odmantic import Model, Field
from typing import List

class CareProfessionalPermission(Model):
    care_professional_id: str = Field(unique=True)
    vendor_id: str
    permissions: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "care_professional_permissions",
        "indexes": [
            {"fields": ["care_professional_id"], "unique": True},
            {"fields": ["vendor_id"]}
        ],
    }
