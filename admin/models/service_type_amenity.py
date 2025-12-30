from odmantic import Model, Field
from datetime import datetime


class ServiceTypeAmenity(Model):
    service_type_id: str     # grooming, boarding, cafe
    amenity_code: str        # AC, CCTV

    is_required: bool = False  # future use (optional)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "service_type_amenities",
        "indexes": [
            {"fields": ["service_type_id"]},
            {"fields": ["service_type_id", "amenity_code"], "unique": True},
        ],
    }
