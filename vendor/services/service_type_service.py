from datetime import datetime
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_service_type import VendorServiceType
from admin.models.service_type import ServiceType
from core.enums import VendorStatus
from bson import ObjectId
from vendor.utils.guards import ensure_vendor_editable

async def select_service_types(
    engine: AIOEngine,
    vendor_id: str,
    service_type_ids: list[str],
):
    # Validate vendor exists
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    ensure_vendor_editable(vendor)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    try:
        service_type_oids = [ObjectId(st_id) for st_id in service_type_ids]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service type id format",
        )

    service_types = await engine.find(
        ServiceType,
        (ServiceType.id.in_(service_type_oids)) &
        (ServiceType.is_active == True)
    )

    if len(service_types) != len(service_type_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more service types are invalid or inactive",
        )

    # Create vendor-service-type mappings (idempotent)
    for st in service_types:
        existing = await engine.find_one(
            VendorServiceType,
            (VendorServiceType.vendor_id == vendor_id)
            & (VendorServiceType.service_type_id == str(st.id)),
        )

        if not existing:
            vst = VendorServiceType(
                vendor_id=vendor_id,
                service_type_id=str(st.id),
            )
            await engine.save(vst)

    # Update vendor status
    vendor.status = VendorStatus.SERVICE_TYPE_SELECTED
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)

    return vendor



async def update_vendor_service_type(
    engine,
    vendor_id: str,
    service_type_id: str,
    is_active: bool,
):
    vst = await engine.find_one(
        VendorServiceType,
        (VendorServiceType.vendor_id == vendor_id)
        & (VendorServiceType.service_type_id == service_type_id),
    )
    ensure_vendor_editable(vst)
    if not vst:
        raise HTTPException(status_code=404, detail="Service type not found")

    vst.is_active = is_active
    vst.updated_at = datetime.utcnow()
    await engine.save(vst)
    return vst
