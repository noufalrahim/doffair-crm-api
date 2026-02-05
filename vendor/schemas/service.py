from pydantic import BaseModel, Field
from typing import List, Optional
from core.enums import ServiceDeliveryMode, DiscountType


class BaseServiceCreateRequest(BaseModel):
    location_id: str
    service_type_id: str

    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    delivery_mode: ServiceDeliveryMode
    
    # Pricing fields
    base_price: float = Field(..., gt=0, description="Base price for the service")
    discount_type: DiscountType = DiscountType.NONE
    discount_value: Optional[float] = Field(None, ge=0, description="Discount amount or percentage")


class ComboServiceCreateRequest(BaseModel):
    location_id: str
    service_type_id: str

    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    included_service_ids: List[str]
    
    # Pricing fields
    base_price: float = Field(..., gt=0, description="Base price for the combo service")
    discount_type: DiscountType = DiscountType.NONE
    discount_value: Optional[float] = Field(None, ge=0, description="Discount amount or percentage")

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
    is_active: bool = True
    
    # Pricing info
    base_price: Optional[float] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    final_price: Optional[float] = None


class VendorServiceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pricing fields (optional for updates)
    base_price: Optional[float] = Field(None, gt=0)
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(None, ge=0)
