from pydantic import BaseModel, Field
from core.enums import DiscountType
from typing import Optional


class PricingCreateRequest(BaseModel):
    service_id: str
    location_id: str

    base_price: float = Field(..., gt=0)

    discount_type: DiscountType = DiscountType.NONE
    discount_value: Optional[float] = None


class PricingResponse(BaseModel):
    service_id: str
    location_id: str

    base_price: float
    discount_type: DiscountType
    discount_value: Optional[float]
    final_price: float
