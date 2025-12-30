from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ServiceAreaType(str, Enum):
    RADIUS = "RADIUS"
    PINCODE = "PINCODE"


class ServiceAreaUpsertRequest(BaseModel):
    service_id: str
    location_id: str

    area_type: ServiceAreaType
    radius_km: Optional[int] = None
    pincodes: Optional[List[str]] = None
