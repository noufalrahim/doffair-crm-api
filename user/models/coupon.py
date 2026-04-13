from odmantic import Model, Field
from typing import Optional
from datetime import datetime

class Coupon(Model):
    code: str = Field(unique=True)
    description: Optional[str] = None
    discount_type: str # 'percentage' or 'fixed'
    discount_value: float
    min_order_value: float = 0.0
    max_discount_amount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    vendor_id: Optional[str] = None # If null, it's a global coupon

    model_config = {
        "collection": "coupons"
    }
