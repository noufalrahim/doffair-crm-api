from pydantic import BaseModel
from typing import Optional


class VendorWorkInfoRequest(BaseModel):
    home_service: bool = False
    centre_service: bool = False
    home_service_radius: Optional[float] = None  # radius in km
    overall_rating: Optional[float] = None
    work_experience: Optional[float] = None


class VendorWorkInfoUpdateRequest(BaseModel):
    home_service: Optional[bool] = None
    centre_service: Optional[bool] = None
    home_service_radius: Optional[float] = None
    overall_rating: Optional[float] = None
    work_experience: Optional[float] = None
