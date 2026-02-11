from odmantic import AIOEngine
from vendor.models.service_area import VendorServiceArea
from vendor.models.vendor import Vendor
from vendor.models.vendor_service import VendorService
from vendor.utils.guards import ensure_vendor_editable
from bson import ObjectId


async def upsert_service_area(
    engine: AIOEngine,
    vendor_id: str,
    payload,
):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    ensure_vendor_editable(vendor)

    service = await engine.find_one(
        VendorService,
        VendorService.id == ObjectId(payload.service_id),
    )

    if not service:
        raise ValueError("Service not found")

    from core.enums import ServiceDeliveryMode
    if service.delivery_mode == ServiceDeliveryMode.CENTER:
        raise ValueError(f"{ServiceDeliveryMode.CENTER} services do not require service area")

    if payload.area_type == "RADIUS" and not payload.radius_km:
        raise ValueError("radius_km required for RADIUS")

    if payload.area_type == "PINCODE" and not payload.pincodes:
        raise ValueError("pincodes required for PINCODE")

    area = await engine.find_one(
        VendorServiceArea,
        VendorServiceArea.service_id == payload.service_id,
    )

    if area:
        area.area_type = payload.area_type
        area.radius_km = payload.radius_km
        area.pincodes = payload.pincodes
    else:
        area = VendorServiceArea(
            vendor_id=vendor_id,
            location_id=payload.location_id,
            service_id=payload.service_id,
            area_type=payload.area_type,
            radius_km=payload.radius_km,
            pincodes=payload.pincodes,
        )

    await engine.save(area)
    return area
