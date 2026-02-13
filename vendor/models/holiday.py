from odmantic import Model, Field
from datetime import datetime
from typing import Optional, List

class HolidaySlot(Model):
    start_time: str
    end_time: str

class Holiday(Model):
    vendor_id: str
    vertical_id: Optional[str] = None
    doctor_id: Optional[str] = None
    
    date: datetime
    name: str
    is_all_day: bool = True
    slots: List[HolidaySlot] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "holidays",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["date"]},
        ],
    }
