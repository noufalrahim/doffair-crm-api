from odmantic import Model, Field
from typing import Optional
from datetime import datetime

from core.enums import CareProfessionalRole


class CareProfessional(Model):
    vendor_id: str
    user_id: str
    location_id: str
    vertical_id: str

    name: str
    role: CareProfessionalRole = CareProfessionalRole.STAFF
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "care_professionals",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["location_id"]},
            {"fields": ["user_id"]},
            {"fields": ["vertical_id"]},
        ],
    }
