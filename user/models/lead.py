from datetime import datetime
from odmantic import Model, Field
from typing import Optional


class Lead(Model):
    """
    Lead model - tracks when a user reveals a vendor's contact
    """
    user_id: str
    vendor_id: str
    vertical_id: str
    
    # User information (cached for quick access)
    user_name: str
    user_phone: str
    user_email: str
    
    # Vendor information (cached for quick access)
    vendor_name: str
    vendor_phone: str
    vendor_email: str
    
    # Metadata
    revealed_at: datetime = Field(default_factory=datetime.utcnow)
    is_contacted: bool = False  # Has vendor reached out to user?
    contacted_at: Optional[datetime] = None
    notes: Optional[str] = None  # Vendor can add notes
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "leads",
        "indexes": [
            {"fields": ["user_id"]},
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
            {"fields": ["revealed_at"]},
            # For checking daily limit
            {"fields": ["user_id", "revealed_at"]},
            # Prevent duplicate leads
            {"fields": ["user_id", "vendor_id", "vertical_id"]},
        ],
    }
