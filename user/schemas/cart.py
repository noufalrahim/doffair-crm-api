from pydantic import BaseModel, Field
from typing import List, Optional
from schemas.common import APIResponse

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int

class CartItemResponse(BaseModel):
    product_id: str
    vendor_id: str
    name: str
    price: float
    quantity: int
    image: Optional[str] = None
    subtotal: float

class CartData(BaseModel):
    items: List[CartItemResponse]
    coupon_code: Optional[str] = None
    total_items: int
    total_price: float
    discount_amount: float = 0.0
    grand_total: float

class CartResponse(APIResponse):
    data: CartData

class ApplyCouponRequest(BaseModel):
    code: str

class CartDeleteResponse(APIResponse):
    message: Optional[str] = None
