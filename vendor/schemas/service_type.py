from pydantic import BaseModel
from typing import List


# ---------------------------------------------------------
# Requests (WRITE) — NO CHANGE
# ---------------------------------------------------------

class VendorServiceTypeSelectRequest(BaseModel):
    service_type_ids: List[str]


class VendorServiceTypeUpdateRequest(BaseModel):
    is_active: bool


# ---------------------------------------------------------
# Responses (READ) — REQUIRED
# ---------------------------------------------------------

class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str


class VendorServiceTypeResponse(BaseModel):
    service_type_id: str
    name: str
    is_active: bool
    images: List[ImageSet] = []
