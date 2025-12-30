from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_admin
from utils.response import success_response

from admin.services.vendor_review import get_vendor_review_snapshot
from admin.services.vendor_approval import approve_vendor, reject_vendor

router = APIRouter(
    prefix="/admin/vendors",
    tags=["Admin - Vendors"],
)


@router.get("/{vendor_id}/review-snapshot")
async def vendor_review_snapshot(
    vendor_id: str,
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    try:
        snapshot = await get_vendor_review_snapshot(engine, vendor_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return success_response(data=snapshot)


@router.post("/{vendor_id}/approve")
async def approve_vendor_api(
    vendor_id: str,
    engine: AIOEngine = Depends(get_engine),
    token: dict = Depends(require_admin),
):
    try:
        vendor = await approve_vendor(engine, vendor_id, token["sub"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Vendor approved successfully",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
        },
    )


@router.post("/{vendor_id}/reject")
async def reject_vendor_api(
    vendor_id: str,
    reason: str,
    engine: AIOEngine = Depends(get_engine),
    token: dict = Depends(require_admin),
):
    try:
        vendor = await reject_vendor(engine, vendor_id, token["sub"], reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Vendor rejected",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
            "reason": reason,
        },
    )