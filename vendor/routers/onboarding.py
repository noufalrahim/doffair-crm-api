from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from odmantic import AIOEngine
import logging
import traceback

from core.database import get_engine
from core.security import require_vendor
from core.media import build_image_set   # ✅ IMAGE HELPER
from vendor.models.vendor import Vendor
from utils.response import success_response
from bson import ObjectId

logger = logging.getLogger(__name__)

from vendor.schemas.onboarding import (
    VendorBasicInfoUpdateRequest,
    VendorSignupRequest,
    VendorBasicInfoRequest,
    VendorOnboardingProgressResponse,
    OtpSendRequest,
    OtpVerifyRequest,
)
from vendor.services.onboarding_service import (
    signup_vendor,
    update_basic_info,
    get_vendor_status,
    update_basic_info_partial,
    get_vendor_onboarding_progress,
)

from core.enums import VendorStatus
from notifications.events.types import EventType, EventSource
from core.otp import send_sms_otp, verify_sms_otp, generate_otp
from notifications.events.publisher import event_publisher
from datetime import datetime   

router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding"],
)

# ---------------------------------------------------------
# OTP Management (Verification before/during signup)
# ---------------------------------------------------------

@router.post("/send-otp")
async def send_onboarding_otp(
    payload: OtpSendRequest,
):
    """Sends BOTH Email and SMS OTPs (same code) for onboarding"""
    otp = generate_otp(6)
    
    # 1. Send SMS OTP via 2Factor.in
    sms_sent = await send_sms_otp(payload.phone, otp)
    
    # 2. Store for Email verification in Redis
    otp_key = f"onboarding_email_otp:{payload.email}"
    try:
        event_publisher._ensure_connection()
        if event_publisher._redis_conn:
            event_publisher._redis_conn.setex(otp_key, 600, otp)
    except Exception as e:
        logger.error(f"Error storing email OTP: {e}")

    # Trigger Email Notification
    event_publisher.publish(
        event_type=EventType.ONBOARDING_OTP,
        source=EventSource.VENDOR_ONBOARDING,
        data={
            "recipient_email": payload.email,
            "otp_code": otp,
            "message": f"Your Doffair onboarding verification code is: {otp}",
            "template_id": "ONBOARDING_OTP"
        }
    )

    return success_response(
        message="OTPs sent successfully",
        data={
            "sms_sent": sms_sent,
            "email_sent": True
        }
    )

@router.post("/verify-otp")
async def verify_onboarding_otp(
    payload: OtpVerifyRequest,
):
    """Verifies both SMS (via 2factor) and Email (via Redis) OTPs"""
    # 1. Verify SMS OTP via 2Factor
    sms_verified = await verify_sms_otp(payload.phone, payload.sms_otp)
    if not sms_verified:
        # Check master override for SMS too
        if payload.sms_otp not in ["1234", "750207"]:
            raise HTTPException(status_code=400, detail="Invalid or expired SMS OTP")
    
    # 2. Verify Email OTP via Redis
    otp_key = f"onboarding_email_otp:{payload.email}"
    redis_available = False
    try:
        event_publisher._ensure_connection()
        if event_publisher._redis_conn is not None:
            try:
                stored_otp = event_publisher._redis_conn.get(otp_key)
                redis_available = True
                if hasattr(stored_otp, 'decode'):
                    stored_otp = stored_otp.decode('utf-8')

                if not stored_otp or payload.email_otp != stored_otp:
                    if payload.email_otp not in ["1234", "750207"]:  # Master override
                        raise HTTPException(status_code=400, detail="Invalid or expired Email OTP")

                # Success — delete used OTP
                try:
                    event_publisher._redis_conn.delete(otp_key)
                except Exception:
                    pass  # Non-critical

            except HTTPException:
                raise
            except Exception as redis_err:
                # Redis connection is stale/broken — fall through to SMS cross-verify
                tb = traceback.format_exc()
                logger.warning(f"Redis get() failed (stale connection?), falling back to SMS cross-verify: {redis_err}\n{tb}")
                redis_available = False

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Verification error (unexpected): {e}\n{tb}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error during verification",
                "type": type(e).__name__,
                "message": str(e),
                "traceback": tb,
            }
        )

    if not redis_available:
        # Fallback: since the same OTP is sent to both SMS and email,
        # and SMS is already verified above, cross-validate email_otp against sms_otp
        logger.warning("Redis unavailable — falling back to SMS cross-verification for Email OTP")
        if payload.email_otp != payload.sms_otp and payload.email_otp not in ["1234", "750207"]:
            raise HTTPException(status_code=400, detail="Invalid or expired Email OTP")

    return success_response(message="Verification successful")


@router.post("/signup")
async def vendor_signup(
    payload: VendorSignupRequest,
    engine: AIOEngine = Depends(get_engine),
):
    vendor = await signup_vendor(engine, payload)

    return success_response(
        message="Vendor signup successful",
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )


# ---------------------------------------------------------
# Vendor Basic Info (CREATE)
# ---------------------------------------------------------

@router.post("/basic-info")
async def vendor_basic_info(
    payload: VendorBasicInfoRequest,
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

    vendor = await update_basic_info(engine, vendor_id, payload, location_id=location_id)

    return success_response(
        message="Basic information saved successfully",
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )


# ---------------------------------------------------------
# Vendor Onboarding Status
# ---------------------------------------------------------

@router.get("/status")
async def vendor_status(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

    vendor = await get_vendor_status(engine, vendor_id)

    return success_response(
        data={
            "vendor_id": str(vendor.id),
            "status": vendor.status,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        }
    )


@router.get("/progress", response_model=dict)
async def get_onboarding_progress(
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Get vendor onboarding progress (percentage and pending steps)
    """
    vendor_id = token.get("vendor_id")
    if not vendor_id:
        raise HTTPException(
            status_code=403,
            detail="Vendor ID not found in token",
        )

    progress = await get_vendor_onboarding_progress(engine, vendor_id, location_id=location_id)

    return success_response(
        message="Onboarding progress retrieved successfully",
        data=progress
    ).model_dump()



# ---------------------------------------------------------
# Vendor Basic Info (UPDATE / PATCH)
# ---------------------------------------------------------

@router.patch("/basic-info")
async def update_vendor_basic_info(
    payload: VendorBasicInfoUpdateRequest,
    location_id: Optional[str] = None, # Add this
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await update_basic_info_partial(engine, vendor_id, payload, location_id=location_id)

    return success_response(
        message="Basic info updated",
        data={
            "vendor_id": vendor_id,
            "logo": build_image_set(vendor.logo_blob_path),  # ✅ IMAGE
        },
    )



@router.post("/submit-for-review")
async def submit_for_review(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404)

    if vendor.status != VendorStatus.SERVICES_CONFIGURED:
        raise HTTPException(
            status_code=400,
            detail="Vendor is not ready for review",
        )

    vendor.status = VendorStatus.UNDER_REVIEW
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)

    return success_response(
        message="Vendor submitted for review",
        data={"status": vendor.status},
    )
