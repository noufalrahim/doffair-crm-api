from datetime import datetime
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_vertical import VendorVertical
from admin.models.vertical import Vertical
from core.enums import VendorStatus
from bson import ObjectId
from vendor.utils.guards import ensure_vendor_editable

async def select_verticals(
    engine: AIOEngine,
    vendor_id: str,
    vertical_ids: list[str],
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
        vertical_oids = [ObjectId(v_id) for v_id in vertical_ids]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vertical id format",
        )

    verticals_data = await engine.find(
        Vertical,
        Vertical.id.in_(vertical_oids)
    )

    if len(verticals_data) != len(vertical_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more verticals are invalid",
        )

    # Create vendor-vertical mappings (idempotent)
    for v in verticals_data:
        existing = await engine.find_one(
            VendorVertical,
            (VendorVertical.vendor_id == vendor_id)
            & (VendorVertical.vertical_id == str(v.id)),
        )

        if not existing:
            vst = VendorVertical(
                vendor_id=vendor_id,
                vertical_id=str(v.id),
                is_active=v.is_active,
            )
            await engine.save(vst)

    # Update vendor status
    vendor.status = VendorStatus.VERTICAL_SELECTED
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)

    return vendor



async def update_vendor_vertical(
    engine,
    vendor_id: str,
    vertical_id: str,
    is_active: bool,
):
    vst = await engine.find_one(
        VendorVertical,
        (VendorVertical.vendor_id == vendor_id)
        & (VendorVertical.vertical_id == vertical_id),
    )
    ensure_vendor_editable(vst)
    if not vst:
        raise HTTPException(status_code=404, detail="Vertical not found")

    vst.is_active = is_active
    vst.updated_at = datetime.utcnow()
    await engine.save(vst)
    return vst


async def delete_vendor_vertical(
    engine: AIOEngine,
    vendor_id: str,
    vertical_id: str,
):
    vst = await engine.find_one(
        VendorVertical,
        (VendorVertical.vendor_id == vendor_id)
        & (VendorVertical.vertical_id == vertical_id),
    )
    
    if not vst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vertical not found",
        )
        
    # Check if vendor is editable
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    ensure_vendor_editable(vendor)

    await engine.delete(vst)
    
    return True
