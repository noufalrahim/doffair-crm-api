from odmantic import AIOEngine
from bson import ObjectId

# ✅ ABSOLUTE imports (THIS IS THE FIX)
from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from vendor.models.vendor_service import VendorService
from vendor.models.vendor_service_type import VendorServiceType

from core.enums import VendorStatus
from core.media import build_image_list



async def get_vendor_review_snapshot(
    engine: AIOEngine,
    vendor_id: str,
) -> dict:
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    # -----------------------------
    # Fetch related entities
    # -----------------------------
    service_types = await engine.find(
        VendorServiceType,
        VendorServiceType.vendor_id == vendor_id,
    )

    locations = await engine.find(
        VendorLocation,
        VendorLocation.vendor_id == vendor_id,
    )

    services = await engine.find(
        VendorService,
        VendorService.vendor_id == vendor_id,
    )

    # -----------------------------
    # Build response blocks
    # -----------------------------
    vendor_block = {
        "vendor_id": str(vendor.id),
        "legal_name": vendor.legal_name,
        "phone": vendor.primary_contact_phone,
        "gst_number": vendor.gst_number,
        "registration_number": vendor.registration_number,
        "logo": build_image_list(
            [vendor.logo_blob_path] if vendor.logo_blob_path else []
        ),
        "created_at": vendor.created_at,
    }

    service_type_block = [
        {
            "service_type_id": st.service_type_id,
            "is_active": st.is_active,
        }
        for st in service_types
    ]

    location_block = [
        {
            "location_id": str(loc.id),
            "name": loc.name,
            "address": loc.address,
            "geo": loc.geo,
        }
        for loc in locations
    ]

    services_block = [
        {
            "service_id": str(s.id),
            "name": s.name,
            "service_kind": s.service_kind,
            "location_id": s.location_id,
            "service_type_id": s.service_type_id,
            "images": build_image_list(s.image_blob_paths),
            "label": s.label,
        }
        for s in services
    ]

    # -----------------------------
    # Readiness check
    # -----------------------------
    ready_for_approval = (
        vendor.status == VendorStatus.UNDER_REVIEW
        and len(service_types) > 0
        and len(locations) > 0
        and len(services) > 0
    )

    return {
        "vendor": vendor_block,
        "service_types": service_type_block,
        "locations": location_block,
        "services": services_block,
        "status": vendor.status,
        "ready_for_approval": ready_for_approval,
    }
