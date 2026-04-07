from datetime import datetime
from odmantic import Model, Field
from typing import Optional, Any
from pydantic import field_validator


class VendorLocation(Model):
    vendor_id: str

    name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"

    latitude: float
    longitude: float

    # Location specific profile info
    legal_name: Optional[str] = None
    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None
    profileImage: Optional[str] = None
    coverPhoto: Optional[str] = None

    # Location specific work info
    home_service: bool = False
    centre_service: bool = False
    home_service_radius: Optional[float] = None  # radius in km
    work_experience: Optional[float] = None

    is_active: bool = True
    is_default: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('address_line_2', mode='before')
    @classmethod
    def validate_address_line_2(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v) if v is not None else None

    model_config = {
        "collection": "vendor_locations",
        "indexes": [
            {"fields": ["vendor_id"]},
        ],
    }
