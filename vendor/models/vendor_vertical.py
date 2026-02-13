from datetime import datetime

from odmantic import Model, Field


class VendorVertical(Model):
    vendor_id: str
    vertical_id: str

    is_active: bool = True

    image_blob_paths: list[str] = []

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_verticals",
        "indexes": [
            {"fields": ["vendor_id", "vertical_id"], "unique": True},
        ],
    }
