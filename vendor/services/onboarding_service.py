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

# New models for progress tracking
from vendor.models.vendor_vertical import VendorVertical
from vendor.models.vendor_location import VendorLocation
from vendor.models.document import Document
from vendor.models.bank_info import BankInfo
from vendor.models.vendor_service import VendorService


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
    
    # Step 2: Basic Info (Exisiting check)
    basic_info_added = bool(vendor.legal_name)

    # Step 3: Basic Overview (New)
    basic_overview_added = bool(vendor.about and vendor.work_experience)

    # Step 4: Work Info (New)
    work_info_added = bool(vendor.home_service or vendor.centre_service)

    # Step 5: Verticals (Refined)
    vertical_count = await engine.count(
        VendorVertical, 
        VendorVertical.vendor_id == vendor_id
    )
    verticals_added = vertical_count > 0

    # Step 6: Location Details (Refined)
    location_count = await engine.count(
        VendorLocation, 
        VendorLocation.vendor_id == vendor_id
    )
    location_added = location_count > 0

    # Step 7: Documents (New)
    document_count = await engine.count(
        Document,
        Document.vendor_id == vendor_id
    )
    documents_added = document_count > 0

    # Step 8: Bank Account (New)
    bank_info_count = await engine.count(
        BankInfo,
        BankInfo.vendor_id == vendor_id
    )
    bank_account_added = bank_info_count > 0

    # Step 9: Services (New)
    service_count = await engine.count(
        VendorService,
        VendorService.vendor_id == vendor_id
    )
    services_added = service_count > 0

    # 3. Calculate Percentage
    steps = [
        ("mobile_verified", mobile_verified),
        ("email_verified", email_verified),
        ("basic_info", basic_info_added),
        ("basic_overview", basic_overview_added),
        ("work_info", work_info_added),
        ("verticals", verticals_added),
        ("location_details", location_added),
        ("documents", documents_added),
        ("bank_account", bank_account_added),
        ("services", services_added)
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
        "basic_overview_added": basic_overview_added,
        "work_info_added": work_info_added,
        "verticals_added": verticals_added,
        "location_added": location_added,
        "documents_added": documents_added,
        "bank_account_added": bank_account_added,
        "services_added": services_added,
        "percentage_completed": percentage,
        "pending_steps": pending
    }
