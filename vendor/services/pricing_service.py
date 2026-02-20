from odmantic import AIOEngine
from datetime import datetime

from vendor.models.vendor_service import VendorService
from vendor.models.vendor import Vendor
from vendor.utils.pricing import calculate_final_price
from core.enums import VendorStatus
from bson import ObjectId


async def upsert_pricing(
    engine: AIOEngine,
    vendor_id: str,
    payload,
):
    # -----------------------------
    # Fetch vendor
    # -----------------------------
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    # -----------------------------
    # Upsert pricing
    # -----------------------------
    service = await engine.find_one(
        VendorService,
        (VendorService.vendor_id == vendor_id)
        & (VendorService.id == ObjectId(payload.service_id))
        & (VendorService.location_id == payload.location_id),
    )

    if not service:
        raise ValueError("Service not found")

    is_first_pricing = service.base_price is None

    service.base_price = payload.base_price
    service.discount_type = payload.discount_type
    service.discount_value = payload.discount_value
    service.updated_at = datetime.utcnow()

    await engine.save(service)

    # -----------------------------
    # 🔥 STATUS TRANSITION (HERE)
    # -----------------------------
    print(is_first_pricing)
    if vendor.status not in {
            VendorStatus.PRICING_CONFIGURED,
            VendorStatus.UNDER_REVIEW,
            VendorStatus.APPROVED,
            VendorStatus.REJECTED,
        }:
        vendor.status = VendorStatus.PRICING_CONFIGURED
        vendor.updated_at = datetime.utcnow()
        await engine.save(vendor)

    return service
