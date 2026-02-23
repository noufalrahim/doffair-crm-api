from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from user.models.user import User
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

    # Also check users collection for duplicate email/phone
    existing_user_email = await engine.find_one(User, User.email == payload.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {payload.email} already exists"
        )

    existing_user_phone = await engine.find_one(User, User.phone == payload.phone)
    if existing_user_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with phone {payload.phone} already exists"
        )

    # Create user record with credentials
    user = User(
        phone=payload.phone,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    await engine.save(user)

    # Create vendor record linked to user
    vendor = Vendor(
        primary_contact_phone=payload.phone,
        primary_contact_email=payload.email,
        user_id=str(user.id),
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
    vendor.profileImage = payload.profileImage
    vendor.coverPhoto = payload.coverPhoto

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


async def get_vendor_onboarding_progress(engine: AIOEngine, vendor_id: str):
    """
    Calculate vendor onboarding progress
    """
    # 1. Fetch Vendor
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # 2. Check Steps
    
    # Step 1: Mobile & Email (Always true if vendor exists, as they are required for creation)
    mobile_verified = True
    email_verified = True  
    
    # Step 2: Basic Info
    # Check if essential fields are present (legal_name is the core field)
    basic_info_added = bool(vendor.legal_name)

    # Step 3: Verticals
    # Check if at least one vertical is configured
    from vendor.models.vendor_vertical import VendorVertical
    vertical_count = await engine.count(
        VendorVertical, 
        VendorVertical.vendor_id == vendor_id
    )
    verticals_added = vertical_count > 0

    # Step 4: Location
    # Check if at least one location is added
    from vendor.models.vendor_location import VendorLocation
    location_count = await engine.count(
        VendorLocation, 
        VendorLocation.vendor_id == vendor_id
    )
    location_added = location_count > 0

    # Step 5: Bank Account
    # TODO: Implement bank account check when model is available
    bank_account_added = False

    # 3. Calculate Percentage
    steps = [
        ("mobile_verified", mobile_verified),
        ("email_verified", email_verified),
        ("basic_info", basic_info_added),
        ("verticals", verticals_added),
        ("location_details", location_added),
        ("bank_account", bank_account_added)
    ]

    total_steps = len(steps)
    completed_steps = sum(1 for _, completed in steps if completed)
    
    if total_steps > 0:
        percentage = round((completed_steps / total_steps) * 100, 2)
    else:
        percentage = 0.0

    # 4. Identify Pending Steps
    pending = [name for name, completed in steps if not completed]

    return {
        "vendor_id": vendor_id,
        "mobile_verified": mobile_verified,
        "email_verified": email_verified,
        "basic_info_added": basic_info_added,
        "verticals_added": verticals_added,
        "location_added": location_added,
        "bank_account_added": bank_account_added,
        "percentage_completed": percentage,
        "pending_steps": pending
    }
