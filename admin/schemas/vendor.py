from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, BeforeValidator
from core.enums import VendorStatus

PyObjectId = Annotated[str, BeforeValidator(str)]


class VendorSchema(BaseModel):
    id: PyObjectId
    legal_name: Optional[str]
    primary_contact_email: str
    primary_contact_phone: str
    status: VendorStatus
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
