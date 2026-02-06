from odmantic import Model, Field
from datetime import datetime
from typing import Optional


class DoctorAvailability(Model):
    service_type_id: str
    doctor_id: Optional[str] = None

    day_of_week: int      # 0 = Monday, 6 = Sunday
    start_time: str       # "10:00"
    end_time: str         # "18:00"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "doctor_availability",
        "indexes": [
            {"fields": ["service_type_id"]},
            {"fields": ["doctor_id"]},
        ],
    }
