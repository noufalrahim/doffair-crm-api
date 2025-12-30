from datetime import datetime
from odmantic import Model, Field
from typing import Optional


class VendorLocation(Model):
    vendor_id: str

    name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"

    latitude: float
    longitude: float

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_locations",
        "indexes": [
            {"fields": ["vendor_id"]},
        ],
    }
