from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StoreItemCreate(BaseModel):
    name: str = Field(..., description="Name of the store item")
    vertical_id: str = Field(..., description="ID of the vertical")
    category: str = Field(..., description="Category of the item")
    stock_quantity: int = Field(..., description="Current stock quantity")
    unit: str = Field(..., description="Unit of measurement")
    base_price: float = Field(..., description="Base price of the item")
    description: Optional[str] = Field(None, description="Optional description")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    images: Optional[List[str]] = Field(None, description="Optional list of image URLs")
    mfd_date: Optional[str] = Field(None, description="Manufacturing date")
    expiry_date: Optional[str] = Field(None, description="Expiry date")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the item")

class StoreItemUpdate(BaseModel):
    name: Optional[str] = None
    vertical_id: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: Optional[int] = None
    unit: Optional[str] = None
    base_price: Optional[float] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    manufacturer: Optional[str] = None
    images: Optional[List[str]] = None
    mfd_date: Optional[str] = None
    expiry_date: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class StoreItemResponse(BaseModel):
    id: str
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
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "vertical_id": "store_vertical_id",
                "name": "Organic Honey",
                "description": "Pure organic forest honey",
                "category": "Groceries",
                "stock_quantity": 50,
                "unit": "bottles",
                "base_price": 250.0,
                "sku": "HONEY-001",
                "manufacturer": "BeeHealth",
                "mfd_date": "2024-01-01",
                "expiry_date": "2025-01-01",
                "images": ["https://example.com/honey.jpg"],
                "tags": ["organic", "natural"],
                "is_active": True,
                "created_at": "2024-03-11T10:00:00Z",
                "updated_at": "2024-03-11T10:00:00Z"
            }
        }

class StoreItemListResponse(BaseModel):
    total: int
    items: List[StoreItemResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "items": [
                    {
                        "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                        "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                        "vertical_id": "store_vertical_id",
                        "name": "Organic Honey",
                        "category": "Groceries",
                        "stock_quantity": 50,
                        "unit": "bottles",
                        "base_price": 250.0,
                        "is_active": True,
                        "created_at": "2024-03-11T10:00:00Z",
                        "updated_at": "2024-03-11T10:00:00Z"
                    }
                ]
            }
        }
