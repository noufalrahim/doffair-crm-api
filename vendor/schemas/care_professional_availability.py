from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CareProfessionalAvailabilityRequest(BaseModel):
    vertical_id: str
    location_id: str
    care_professional_id: str
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(..., examples=["09:00"])
    end_time: str = Field(..., examples=["17:00"])


class CareProfessionalAvailabilityResponse(BaseModel):
    id: str
    vendor_id: str
    vertical_id: str
    location_id: str
    care_professional_id: str
    day_of_week: int
    start_time: str
    end_time: str
    created_at: datetime
