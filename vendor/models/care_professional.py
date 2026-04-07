from odmantic import Model, Field
from typing import Optional, Any
from datetime import datetime
from pydantic import field_validator

from core.enums import CareProfessionalRole


class CareProfessional(Model):
    vendor_id: str
    user_id: str
    location_id: str
    vertical_id: str

    name: str
    role: CareProfessionalRole = CareProfessionalRole.STAFF
    is_active: bool = True

    specialization: Optional[str] = None
    years_of_experience: Optional[str] = None
    consultation_fee: Optional[str] = None
    license_number: Optional[str] = None
    profile_image: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('years_of_experience', mode='before')
    @classmethod
    def validate_years_of_experience(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return str(v) if v is not None else None

    @field_validator('consultation_fee', mode='before')
    @classmethod
    def validate_consultation_fee(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return str(v) if v is not None else None

    model_config = {
        "collection": "care_professionals",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["location_id"]},
            {"fields": ["user_id"]},
            {"fields": ["vertical_id"]},
        ],
    }
