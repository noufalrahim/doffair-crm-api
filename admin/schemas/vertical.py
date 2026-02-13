from pydantic import BaseModel, Field
from core.enums import ServiceMode
from typing import List, Optional
from schemas.common import APIResponse



class ImageSet(BaseModel):
    original: str
    medium: str
    thumbnail: str



class VerticalCreate(BaseModel):
    code: List[str] = Field(..., examples=[["grooming", "groomer"]])
    display_name: str = Field(..., examples=["Pet Grooming"])
    description: Optional[str] = None
    mode: ServiceMode
    url: Optional[str] = None
    icon: Optional[str] = None
    priority: int = 100


class VerticalUpdate(BaseModel):
    code: Optional[List[str]] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    mode: Optional[ServiceMode] = None
    is_active: Optional[bool] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    priority: Optional[int] = None


class VerticalResponse(BaseModel):
    id: str
    code: List[str]
    display_name: str
    description: Optional[str]
    mode: ServiceMode
    is_active: bool
    image_blob_paths: List[str] = []  # Changed from ImageSet to match model
    url: Optional[str] = None
    icon: Optional[str] = None
    priority: int = 100

    class Config:
        from_attributes = True


class VerticalCreateResponse(APIResponse):
    data: VerticalResponse


class VerticalListResponse(APIResponse):
    data: List[VerticalResponse]


class VerticalSingleResponse(APIResponse):
    data: VerticalResponse
