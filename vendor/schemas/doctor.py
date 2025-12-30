from pydantic import BaseModel


class DoctorCreateRequest(BaseModel):
    location_id: str
    name: str
    specialization: str
    descrption: str


class DoctorAvailabilityRequest(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
