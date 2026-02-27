from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class AvailabilitySlot(BaseModel):
    start_time: str # "09:00 AM"
    end_time: str   # "09:30 AM"
    is_open: bool
    is_available: bool = True

class AvailabilitySection(BaseModel):
    slot: str  # "morning", "afternoon", "evening", "night"
    slot_period: List[AvailabilitySlot]

class DailyAvailabilityResponse(BaseModel):
    date: date
    is_holiday: bool
    holiday_name: Optional[str] = None
    sections: List[AvailabilitySection]
