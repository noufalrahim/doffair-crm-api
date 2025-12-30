from pydantic import BaseModel, Field
from core.enums import ServiceMode
from typing import List, Optional
from schemas.common import APIResponse

from typing import List, Optional
from pydantic import BaseModel


class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str



class ServiceTypeCreate(BaseModel):
    code: str = Field(..., examples=["grooming"])
    display_name: str = Field(..., examples=["Pet Grooming"])
    description: Optional[str] = None
    mode: ServiceMode


class ServiceTypeResponse(BaseModel):
    id: str
    code: str
    display_name: str
    description: Optional[str]
    mode: ServiceMode
    is_active: bool
    image_blob_paths: List[ImageSet] = []  # ✅ NEW

    class Config:
        from_attributes = True



class ServiceTypeCreateResponse(APIResponse):
    data: ServiceTypeResponse


class ServiceTypeListResponse(APIResponse):
    data: List[ServiceTypeResponse]
