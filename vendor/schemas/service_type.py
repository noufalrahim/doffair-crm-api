from pydantic import BaseModel
from typing import List, Optional


# ---------------------------------------------------------
# Requests (WRITE) — NO CHANGE
# ---------------------------------------------------------

class VendorServiceTypeSelectRequest(BaseModel):
    service_type_ids: List[str]


class VendorServiceTypeUpdateRequest(BaseModel):
    is_active: bool


class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str


class VendorServiceTypeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    images: List[ImageSet] = []
    is_active: bool
