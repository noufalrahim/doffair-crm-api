from fastapi import HTTPException
from vendor.models.vendor import Vendor
from core.enums import VendorStatus


def ensure_vendor_editable(vendor: Vendor):
    """
    Prevents vendor-side edits once vendor is under review or finalized.
    """
    if vendor.status in {
        VendorStatus.UNDER_REVIEW,
        VendorStatus.APPROVED,
        VendorStatus.REJECTED,
    }:
        raise HTTPException(
            status_code=400,
            detail="Vendor profile is locked and cannot be modified",
        )
