from pydantic import BaseModel
from typing import List


class VendorAmenityUpsertRequest(BaseModel):
    location_id: str
    service_type_id: str
    amenity_codes: List[str]


class VendorAmenityResponse(BaseModel):
    location_id: str
    service_type_id: str
    amenity_codes: List[str]
