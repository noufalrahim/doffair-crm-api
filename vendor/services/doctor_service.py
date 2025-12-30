from odmantic import AIOEngine
from datetime import datetime

from vendor.models.doctor import Doctor
from vendor.models.vendor import Vendor
from vendor.utils.guards import ensure_vendor_editable

from bson import ObjectId


async def create_doctor(
    engine: AIOEngine,
    vendor_id: str,
    payload,
):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise ValueError("Vendor not found")

    ensure_vendor_editable(vendor)

    doctor = Doctor(
        vendor_id=vendor_id,
        location_id=payload.location_id,
        name=payload.name,
        specialization=payload.specialization,
    )

    await engine.save(doctor)
    return doctor
