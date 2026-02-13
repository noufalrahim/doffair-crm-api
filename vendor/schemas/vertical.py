from pydantic import BaseModel
from typing import List, Optional


# ---------------------------------------------------------
# Requests (WRITE) — NO CHANGE
# ---------------------------------------------------------

class VendorVerticalSelectRequest(BaseModel):
    vertical_ids: List[str]


class VendorVerticalUpdateRequest(BaseModel):
    is_active: bool


class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str


class VendorVerticalResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    images: List[ImageSet] = []
    is_active: bool
