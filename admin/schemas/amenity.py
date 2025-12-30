from pydantic import BaseModel
from typing import Optional, List


class AmenityCreateRequest(BaseModel):
    code: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class AmenityResponse(BaseModel):
    code: str
    display_name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: bool


class ServiceTypeAmenityMapRequest(BaseModel):
    amenity_codes: List[str]
