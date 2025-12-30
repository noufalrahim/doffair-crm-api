from datetime import datetime

from odmantic import Model, Field


class VendorServiceType(Model):
    vendor_id: str
    service_type_id: str

    is_active: bool = True

    image_blob_paths: list[str] = []

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_service_types",
        "indexes": [
            {"fields": ["vendor_id", "service_type_id"], "unique": True},
        ],
    }
