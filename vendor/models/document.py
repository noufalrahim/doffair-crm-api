from odmantic import Model, Field
from datetime import datetime
from typing import Optional

class Document(Model):
    """
    Vendor document record
    """
    vendor_id: str
    name: str
    link: str
    type: str  # e.g., kyc, invoice, agreement, other
    description: Optional[str] = None
    
    is_verified: bool = False
    message: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "documents",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vendor_id", "type"]},
            {"fields": ["vendor_id", "name"]},
            {"fields": ["is_active"]},
        ],
    }
