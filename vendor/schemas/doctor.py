from pydantic import BaseModel
from typing import Optional


class DoctorCreateRequest(BaseModel):
    location_id: str
    name: str
    specialization: str
    descrption: str


class DoctorAvailabilityRequest(BaseModel):
    vertical_id: str
    doctor_id: Optional[str] = None
    day_of_week: int
    start_time: str
    end_time: str
