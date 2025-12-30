from odmantic import Model
from typing import List, Optional
from enum import Enum


class ServiceAreaType(str, Enum):
    RADIUS = "RADIUS"
    PINCODE = "PINCODE"


class VendorServiceArea(Model):
    vendor_id: str
    location_id: str
    service_id: str

    area_type: ServiceAreaType

    # If RADIUS
    radius_km: Optional[int] = None

    # If PINCODE
    pincodes: Optional[List[str]] = None

    model_config = {
        "collection": "vendor_service_areas",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["service_id"], "unique": True},
        ],
    }
