from odmantic import Model, Field
from datetime import datetime


class Doctor(Model):
    vendor_id: str
    location_id: str

    name: str
    specialization: str

    description: str = ""

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "doctors",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["location_id"]},
        ],
    }
