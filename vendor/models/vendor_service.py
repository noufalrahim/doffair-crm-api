from datetime import datetime
from typing import List, Optional

from odmantic import Model, Field
from core.enums import ServiceDeliveryMode


class VendorService(Model):
    vendor_id: str
    service_type_id: str
    location_id: str
    name: str
    service_kind: str  # BASE | COMBO

    # 🔥 REQUIRED FOR IMAGE PIPELINE
    image_blob_paths: List[str] = []

    label: Optional[str] = None
    delivery_mode: ServiceDeliveryMode 
    is_active: bool = True  # Active/Inactive state for services

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_services",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["service_type_id"]},
        ],
    }
