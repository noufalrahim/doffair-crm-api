from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.schemas.onboarding import VendorSignupRequest, VendorBasicInfoRequest
from core.enums import VendorStatus
from admin.utils.password import hash_password  # reuse existing util
from vendor.utils.guards import ensure_vendor_editable


async def signup_vendor(engine: AIOEngine, payload: VendorSignupRequest) -> Vendor:
    # Check for existing vendor by phone OR email
    existing_phone = await engine.find_one(
        Vendor,
        Vendor.primary_contact_phone == payload.phone
    )
    
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vendor with phone number {payload.phone} already exists"
        )
    
    existing_email = await engine.find_one(
        Vendor,
        Vendor.primary_contact_email == payload.email
    )
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vendor with email {payload.email} already exists"
        )

    # Create new vendor
    vendor = Vendor(
        primary_contact_phone=payload.phone,
        primary_contact_email=payload.email,
        password_hash=hash_password(payload.password),
        status=VendorStatus.PHONE_VERIFIED,
    )

    await engine.save(vendor)
    return vendor


async def update_basic_info(
    engine: AIOEngine,
    vendor_id: str,
    payload: VendorBasicInfoRequest,
) -> Vendor:
    try:
        vendor_oid = ObjectId(vendor_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vendor id",
        )

    vendor = await engine.find_one(Vendor, Vendor.id == vendor_oid)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    vendor.legal_name = payload.legal_name
    vendor.gst_number = payload.gst_number
    vendor.business_registration_number = payload.business_registration_number

    vendor.status = VendorStatus.BASIC_INFO_SUBMITTED
    vendor.updated_at = datetime.utcnow()

    await engine.save(vendor)
    return vendor


async def get_vendor_status(engine: AIOEngine, vendor_id: str) -> Vendor:
    try:
        vendor_oid = ObjectId(vendor_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vendor id",
        )

    vendor = await engine.find_one(Vendor, Vendor.id == vendor_oid)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    return vendor



async def update_basic_info_partial(
    engine,
    vendor_id: str,
    payload,
):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    ensure_vendor_editable(vendor)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(vendor, field, value)

    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)
    return vendor
