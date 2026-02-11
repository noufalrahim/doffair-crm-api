from odmantic import Model, Field
from datetime import datetime
from typing import Optional


class DoctorAvailability(Model):
    vendor_id: str
    service_type_id: str
    doctor_id: Optional[str] = None

    day_of_week: int      # 0 = Monday, 6 = Sunday
    start_time: str       # "10:00"
    end_time: str         # "18:00"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "availability",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["service_type_id"]},
            {"fields": ["doctor_id"]},
        ],
    }
