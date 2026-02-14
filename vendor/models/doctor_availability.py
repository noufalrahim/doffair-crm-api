from odmantic import Model, Field
from datetime import datetime
from typing import Optional


class Availability(Model):
    vendor_id: str
    vertical_id: str
    location_id: Optional[str] = None
    care_professional_id: Optional[str] = None
    doctor_id: Optional[str] = None # Keeping for legacy support if needed, but care_professional_id is primary

    day_of_week: int      # 0 = Monday, 6 = Sunday
    start_time: str       # "10:00"
    end_time: str         # "18:00"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "availability",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
            {"fields": ["location_id"]},
            {"fields": ["care_professional_id"]},
            {"fields": ["doctor_id"]},
        ],
    }
