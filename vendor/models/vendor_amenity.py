from odmantic import Model, Field
from typing import List
from datetime import datetime


class VendorAmenity(Model):
    vendor_id: str
    location_id: str
    vertical_id: str

    amenity_codes: List[str]

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_amenities",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vendor_id", "location_id", "vertical_id"], "unique": True},
        ],
    }
