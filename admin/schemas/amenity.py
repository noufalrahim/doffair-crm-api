from typing import List, Optional
from pydantic import BaseModel
from schemas.common import APIResponse


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


class VerticalAmenityMapRequest(BaseModel):
    amenity_codes: List[str]


class AmenityCreateResponse(APIResponse):
    data: AmenityResponse


class AmenityListResponse(APIResponse):
    data: List[AmenityResponse]


class AmenityMapResponse(APIResponse):
    data: dict
