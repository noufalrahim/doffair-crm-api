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

    images: List[str] = []
    
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    label: Optional[str] = None
    delivery_mode: Optional[ServiceDeliveryMode] = None
    dog_sizes: List[DogSize] = []
    included_service_ids: List[str] = []
    is_active: bool = True

    base_price: Optional[float] = None
    discount_type: Optional[str] = "NONE"
    discount_value: Optional[float] = None

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

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: Any) -> Any:
        if v is None:
            return None
        # Handle cases where description might be an enum value
        if isinstance(v, ServiceDeliveryMode):
            return v.value
        return str(v)

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def validate_duration(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0 # Default to 0 if invalid

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_services",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
        ],
    }
