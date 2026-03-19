from datetime import datetime
from odmantic import Model, Field
from typing import Optional

class VendorSession(Model):
    vendor_id: str = Field(index=True)
    jti: str = Field(unique=True, index=True)  # JWT ID
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # Desktop, Mobile, Tablet
    os: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: str
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendor_sessions"
    }
