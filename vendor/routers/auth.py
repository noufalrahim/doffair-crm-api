from fastapi import APIRouter, Depends, Request
from odmantic import AIOEngine

from core.database import get_engine
from utils.response import success_response

from vendor.schemas.auth import VendorLoginRequest
from vendor.services.auth_service import login_vendor

router = APIRouter(
    prefix="/vendor/auth",
    tags=["Vendor Auth"],
)


@router.post("/login")
async def vendor_login(
    payload: VendorLoginRequest,
    request: Request,
    engine: AIOEngine = Depends(get_engine),
):
    user_agent = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"
    
    vendor, response_data = await login_vendor(engine, payload, user_agent, ip_address)

    return success_response(
        message="Login successful",
        data=response_data,
    )
