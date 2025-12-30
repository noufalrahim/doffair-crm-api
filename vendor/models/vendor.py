from datetime import datetime
from typing import Optional

from odmantic import Model, Field
from core.enums import VendorStatus


class Vendor(Model):
    legal_name: Optional[str] = None

    primary_contact_email: str = Field(unique=True)
    primary_contact_phone: str = Field(unique=True)

    password_hash: str

    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None

    logo_blob_path: Optional[str] = None

    status: VendorStatus = VendorStatus.PHONE_VERIFIED
    is_active: bool = True

    status: VendorStatus

    # 🔥 Approval metadata
    reviewed_by: Optional[str] = None   # admin user id
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendors"
    }
