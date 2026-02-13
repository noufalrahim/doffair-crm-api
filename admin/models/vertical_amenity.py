from odmantic import Model, Field
from datetime import datetime


class VerticalAmenity(Model):
    vertical_id: str     # grooming, boarding, cafe
    amenity_code: str        # AC, CCTV

    is_required: bool = False  # future use (optional)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vertical_amenities",
        "indexes": [
            {"fields": ["vertical_id"]},
            {"fields": ["vertical_id", "amenity_code"], "unique": True},
        ],
    }
