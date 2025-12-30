from odmantic import Model, Field
from datetime import datetime


class DoctorAvailability(Model):
    doctor_id: str

    day_of_week: int      # 0 = Monday, 6 = Sunday
    start_time: str       # "10:00"
    end_time: str         # "18:00"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "doctor_availability",
        "indexes": [
            {"fields": ["doctor_id"]},
        ],
    }
