from pydantic import BaseModel, Field
from typing import List, Optional
from core.enums import ServiceDeliveryMode


class BaseServiceCreateRequest(BaseModel):
    location_id: str
    service_type_id: str

    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    delivery_mode: ServiceDeliveryMode


class ComboServiceCreateRequest(BaseModel):
    location_id: str
    service_type_id: str

    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    included_service_ids: List[str]

# ---------------------------------------------------------

class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str

class VendorServiceResponse(BaseModel):
    id: str
    name: str
    service_kind: str
    location_id: str
    service_type_id: str
    images: List[ImageSet] = []


class VendorServiceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
