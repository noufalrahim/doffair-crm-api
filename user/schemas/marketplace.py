from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.common import APIResponse

class ProductResponse(BaseModel):
    id: str
    vendor_id: str
    name: str
    description: Optional[str] = None
    category: str
    base_price: float
    images: Optional[List[str]] = None
    stock_quantity: int
    is_active: bool

class StoreResponse(BaseModel):
    id: str
    legal_name: Optional[str] = None
    about: Optional[str] = None
    logo: Optional[str] = None
    rating: Optional[float] = None
    is_verified: bool

class MarketplaceSearchData(BaseModel):
    products: List[ProductResponse]
    stores: List[StoreResponse]

class MarketplaceSearchResponse(APIResponse):
    data: MarketplaceSearchData

class FilterData(BaseModel):
    categories: List[str]
    price_min: float
    price_max: float
    vendors: List[StoreResponse]

class FilterResponse(APIResponse):
    data: FilterData

class CouponResponse(BaseModel):
    id: str
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_order_value: float
    end_date: datetime

class CouponListResponse(APIResponse):
    data: List[CouponResponse]

class StoreDetailsResponse(APIResponse):
    data: StoreResponse

class StoreProductsResponse(APIResponse):
    data: List[ProductResponse]

class ProductDetailsResponse(APIResponse):
    data: ProductResponse
