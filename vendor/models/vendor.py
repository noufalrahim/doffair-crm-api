from datetime import datetime
from typing import Optional, List

from odmantic import Model, Field
from core.enums import VendorStatus


class Vendor(Model):
    legal_name: Optional[str] = None

    primary_contact_email: str = Field(unique=True)
    primary_contact_phone: str = Field(unique=True)

    user_id: Optional[str] = None  # link to users collection

    gst_number: Optional[str] = None
    business_registration_number: Optional[str] = None

    logo_blob_path: Optional[str] = None
    profileImage: Optional[str] = None
    coverPhoto: Optional[str] = None
    gallery: List[str] = []

    # Basic info fields
    about: Optional[str] = None
    alternative_phone: Optional[str] = None
    work_experience: Optional[float] = None

    # Work-related info
    home_service: bool = False
    centre_service: bool = False
    home_service_radius: Optional[float] = None  # radius in km
    overall_rating: Optional[float] = None

    status: VendorStatus = VendorStatus.PHONE_VERIFIED
    is_active: bool = True

    # 🔥 Approval metadata
    reviewed_by: Optional[str] = None   # admin user id
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "vendors",
        "parse_doc_with_default_factories": True
    }
