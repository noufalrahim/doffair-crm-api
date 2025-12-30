from odmantic import AIOEngine
from datetime import datetime

from vendor.models.service_pricing import ServicePricing
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
    pricing = await engine.find_one(
        ServicePricing,
        (ServicePricing.vendor_id == vendor_id)
        & (ServicePricing.service_id == payload.service_id)
        & (ServicePricing.location_id == payload.location_id),
    )

    is_first_pricing = pricing is None

    if pricing:
        pricing.base_price = payload.base_price
        pricing.discount_type = payload.discount_type
        pricing.discount_value = payload.discount_value
        pricing.updated_at = datetime.utcnow()
    else:
        pricing = ServicePricing(
            vendor_id=vendor_id,
            service_id=payload.service_id,
            location_id=payload.location_id,
            base_price=payload.base_price,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
        )

    await engine.save(pricing)

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

    return pricing
