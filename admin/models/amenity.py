from odmantic import Model, Field
from typing import Optional
from datetime import datetime


class Amenity(Model):
    code: str                # e.g. AC, CCTV, WIFI
    display_name: str        # e.g. "Air Conditioned Rooms"
    description: Optional[str] = None

    icon: Optional[str] = None  # frontend icon key
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "amenities",
        "indexes": [
            {"fields": ["code"], "unique": True},
        ],
    }
