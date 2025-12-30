from odmantic import Model, Field
from typing import Optional
from datetime import datetime

from core.enums import DiscountType


class ServicePricing(Model):
    vendor_id: str
    service_id: str
    location_id: str

    base_price: float

    discount_type: DiscountType = DiscountType.NONE
    discount_value: Optional[float] = None

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "service_pricing",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["service_id", "location_id"], "unique": True},
        ],
    }
