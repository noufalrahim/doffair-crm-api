from odmantic import Model, EmbeddedModel, Field
from typing import List, Optional
from datetime import datetime

class CartItem(EmbeddedModel):
    product_id: str
    vendor_id: str
    quantity: int
    name: str # Cache name and price
    price: float
    image: Optional[str] = None

class Cart(Model):
    user_id: str = Field(unique=True)
    items: List[CartItem] = []
    coupon_code: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "carts"
    }
