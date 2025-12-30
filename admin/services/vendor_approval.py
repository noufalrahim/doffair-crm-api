from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime

from vendor.models.vendor import Vendor
from core.enums import VendorStatus


async def approve_vendor(
    engine: AIOEngine,
    vendor_id: str,
    admin_id: str,
):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    if vendor.status != VendorStatus.UNDER_REVIEW:
        raise ValueError("Vendor is not under review")

    vendor.status = VendorStatus.APPROVED
    vendor.reviewed_by = admin_id
    vendor.reviewed_at = datetime.utcnow()
    vendor.rejection_reason = None

    await engine.save(vendor)
    return vendor


async def reject_vendor(
    engine: AIOEngine,
    vendor_id: str,
    admin_id: str,
    reason: str,
):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    vendor.status = VendorStatus.REJECTED
    vendor.reviewed_by = admin_id
    vendor.reviewed_at = datetime.utcnow()
    vendor.rejection_reason = reason

    await engine.save(vendor)
    return vendor
