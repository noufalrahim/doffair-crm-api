from odmantic import AIOEngine
from datetime import datetime

from vendor.models.vendor_amenity import VendorAmenity
from vendor.models.vendor import Vendor
from admin.models.amenity import Amenity
from admin.models.service_type_amenity import ServiceTypeAmenity
from vendor.utils.guards import ensure_vendor_editable
from bson import ObjectId


async def upsert_vendor_amenities(
    engine: AIOEngine,
    vendor_id: str,
    payload,
):
    # -----------------------------
    # Fetch vendor & freeze check
    # -----------------------------
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    ensure_vendor_editable(vendor)

    # -----------------------------
    # Fetch allowed amenities
    # -----------------------------
    allowed_mappings = await engine.find(
        ServiceTypeAmenity,
        ServiceTypeAmenity.service_type_id == payload.service_type_id,
    )
    allowed_codes = {m.amenity_code for m in allowed_mappings}

    if not allowed_codes:
        raise ValueError("No amenities configured for this service type")

    # -----------------------------
    # Fetch active amenities
    # -----------------------------
    active_amenities = await engine.find(
        Amenity,
        Amenity.code.in_(list(allowed_codes)) & (Amenity.is_active == True),
    )
    active_codes = {a.code for a in active_amenities}

    # -----------------------------
    # Validate vendor selection
    # -----------------------------
    invalid = set(payload.amenity_codes) - active_codes
    if invalid:
        raise ValueError(f"Invalid or inactive amenities selected: {invalid}")

    # -----------------------------
    # Upsert vendor amenities
    # -----------------------------
    record = await engine.find_one(
        VendorAmenity,
        (VendorAmenity.vendor_id == vendor_id)
        & (VendorAmenity.location_id == payload.location_id)
        & (VendorAmenity.service_type_id == payload.service_type_id),
    )

    if record:
        record.amenity_codes = payload.amenity_codes
        record.updated_at = datetime.utcnow()
    else:
        record = VendorAmenity(
            vendor_id=vendor_id,
            location_id=payload.location_id,
            service_type_id=payload.service_type_id,
            amenity_codes=payload.amenity_codes,
        )

    await engine.save(record)
    return record
