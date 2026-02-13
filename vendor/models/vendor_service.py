from datetime import datetime
from typing import List, Optional

from odmantic import Model, Field
from core.enums import ServiceDeliveryMode, DogSize
from pydantic import field_validator
from typing import Any


class VendorService(Model):
    vendor_id: str
    vertical_id: str
    location_id: str
    name: str
    service_kind: str

    image_blob_paths: List[str] = []
    
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    label: Optional[str] = None
    delivery_mode: Optional[ServiceDeliveryMode] = None
    dog_sizes: List[DogSize] = []
    included_service_ids: List[str] = []
    is_active: bool = True

    @field_validator("delivery_mode", mode="before")
    @classmethod
    def map_delivery_mode(cls, v: Any) -> Any:
        mapping = {
            "CENTER": ServiceDeliveryMode.CENTER,
            "HOME": ServiceDeliveryMode.HOME,
            "BOTH": ServiceDeliveryMode.BOTH,
        }
        if v in mapping:
            return mapping[v]
        return v

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_services",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
        ],
    }
