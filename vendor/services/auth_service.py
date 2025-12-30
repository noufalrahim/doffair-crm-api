from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.schemas.auth import VendorLoginRequest
from admin.utils.password import verify_password
from core.security import create_access_token
from core.enums import Role, VendorRole


async def authenticate_vendor(
    engine: AIOEngine,
    payload: VendorLoginRequest,
) -> Vendor:
    vendor = await engine.find_one(
        Vendor,
        Vendor.primary_contact_email == payload.email,
    )

    if not vendor or not vendor.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(payload.password, vendor.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return vendor



async def login_vendor(
    engine: AIOEngine,
    payload: VendorLoginRequest,
):
    vendor = await authenticate_vendor(engine, payload)

    token = create_access_token(
        subject=str(vendor.id),              # required
        role=Role.VENDOR,                    # required
        vendor_id=str(vendor.id),             # vendor context
        vendor_role=VendorRole.ADMIN,  # enum, not string
    )

    return vendor, token
