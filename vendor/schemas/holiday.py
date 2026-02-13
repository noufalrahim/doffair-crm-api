from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class HolidaySlotSchema(BaseModel):
    start_time: str = Field(..., description="HH:MM format")
    end_time: str = Field(..., description="HH:MM format")

class HolidayCreateRequest(BaseModel):
    vertical_id: Optional[str] = None
    doctor_id: Optional[str] = None
    date: datetime
    name: str = Field(..., min_length=1, max_length=100)
    is_all_day: bool = True
    slots: List[HolidaySlotSchema] = Field(default_factory=list)

class HolidayResponse(BaseModel):
    id: str
    vertical_id: Optional[str]
    doctor_id: Optional[str]
    date: datetime
    name: str
    is_all_day: bool
    slots: List[HolidaySlotSchema]
    created_at: datetime
