from odmantic import AIOEngine
from fastapi import HTTPException, status
from bson import ObjectId

from vendor.models.vendor import Vendor
from user.models.user import User
from vendor.schemas.auth import VendorLoginRequest
from admin.utils.password import verify_password
from core.security import create_access_token
from core.enums import Role, VendorRole


from vendor.models.care_professional import CareProfessional

async def authenticate_vendor(
    engine: AIOEngine,
    payload: VendorLoginRequest,
) -> dict:
    user = await engine.find_one(
        User,
        User.email == payload.email,
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if user is a Vendor Admin
    vendor = await engine.find_one(
        Vendor,
        (Vendor.user_id == str(user.id)) | (Vendor.primary_contact_email == user.email),
    )

    if vendor and vendor.is_active:
        return {"type": "vendor", "vendor": vendor}

    # Check if user is a care professional
    care_prof = await engine.find_one(
        CareProfessional,
        CareProfessional.user_id == str(user.id),
    )

    if care_prof and care_prof.is_active:
        vendor = await engine.find_one(
            Vendor,
            Vendor.id == ObjectId(care_prof.vendor_id),
        )
        if vendor and vendor.is_active:
            return {"type": "care_professional", "care_professional": care_prof, "vendor": vendor}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access",
    )


async def login_vendor(
    engine: AIOEngine,
    payload: VendorLoginRequest,
):
    auth_result = await authenticate_vendor(engine, payload)
    
    vendor = auth_result["vendor"]

    if auth_result["type"] == "vendor":
        token = create_access_token(
            subject=str(vendor.id),
            role=Role.VENDOR,
            vendor_id=str(vendor.id),
            vendor_role=VendorRole.ADMIN,
        )
    else:
        # Care professional
        care_prof = auth_result["care_professional"]
        try:
            v_role = VendorRole(care_prof.role.value)
        except ValueError:
            v_role = VendorRole.STAFF
            
        token = create_access_token(
            subject=str(vendor.id),
            role=Role.VENDOR,
            vendor_id=str(vendor.id),
            vendor_role=v_role,
            care_professional_id=str(care_prof.id)
        )

    return vendor, token
