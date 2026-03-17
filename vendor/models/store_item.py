from odmantic import Model, Field
from datetime import datetime
from typing import Optional, List

class StoreItem(Model):
    """
    Store item master record managed by vendor
    """
    vendor_id: str
    vertical_id: str
    name: str
    description: Optional[str] = None
    category: str
    stock_quantity: int
    unit: str
    base_price: float
    sku: Optional[str] = None
    manufacturer: Optional[str] = None
    images: Optional[List[str]] = None
    mfd_date: Optional[str] = None
    expiry_date: Optional[str] = None
    tags: Optional[List[str]] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "store_items",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
            {"fields": ["vendor_id", "name"]},
            {"fields": ["vertical_id", "name"]},
            {"fields": ["sku"]},
            {"fields": ["is_active"]},
        ],
    }
