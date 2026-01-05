from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_user, require_vendor
from utils.response import success_response
from user.schemas.lead import (
    RevealMobileRequest,
    RevealMobileResponse,
    LeadResponse,
    MarkContactedRequest,
)
from user.services.lead_service import (
    reveal_vendor_contact,
    get_vendor_leads,
    mark_lead_contacted,
    get_user_leads,
    check_daily_limit,
)


router = APIRouter(
    prefix="/leads",
    tags=["Lead Generation"],
)


# ---------------------------------------------------------
# User Endpoints
# ---------------------------------------------------------

@router.get("/my-daily-limit")
async def check_my_daily_limit(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Check how many leads user has created today
    """
    user_id = token.get("user_id")
    can_reveal, current_count = await check_daily_limit(engine, user_id)
    
    return success_response(
        data={
            "current_count": current_count,
            "daily_limit": 5,
            "remaining": 5 - current_count if can_reveal else 0,
            "can_reveal_more": can_reveal,
        }
    )


@router.post("/reveal-mobile")
async def reveal_vendor_mobile(
    payload: RevealMobileRequest,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    User reveals vendor's mobile number
    - Creates a lead
    - Returns vendor contact details
    - Max 5 reveals per day per user
    """
    user_id = token.get("user_id")
    
    lead, service_type = await reveal_vendor_contact(
        engine=engine,
        user_id=user_id,
        vendor_id=payload.vendor_id,
        service_type_id=payload.service_type_id,
    )
    
    return RevealMobileResponse(
        lead_id=str(lead.id),
        vendor_name=lead.vendor_name,
        vendor_phone=lead.vendor_phone,
        vendor_email=lead.vendor_email,
        service_type_name=service_type.display_name,
        message=f"Contact revealed successfully! You can now reach out to {lead.vendor_name}.",
    )


@router.get("/my-leads")
async def get_my_leads(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Get all leads created by the user
    """
    user_id = token.get("user_id")
    
    leads_with_service_types = await get_user_leads(engine, user_id, limit, skip)
    
    return success_response(
        data=[
            LeadResponse(
                lead_id=str(lead.id),
                user_name=lead.user_name,
                user_phone=lead.user_phone,
                user_email=lead.user_email,
                service_type_name=service_type.display_name if service_type else "Unknown",
                revealed_at=lead.revealed_at,
                is_contacted=lead.is_contacted,
                contacted_at=lead.contacted_at,
                notes=lead.notes,
            )
            for lead, service_type in leads_with_service_types
        ]
    )


# ---------------------------------------------------------
# Vendor Endpoints
# ---------------------------------------------------------

@router.get("/vendor/my-leads")
async def get_vendor_my_leads(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Vendor views all their leads
    """
    vendor_id = token.get("vendor_id")
    
    leads_with_service_types = await get_vendor_leads(engine, vendor_id, limit, skip)
    
    return success_response(
        data=[
            LeadResponse(
                lead_id=str(lead.id),
                user_name=lead.user_name,
                user_phone=lead.user_phone,
                user_email=lead.user_email,
                service_type_name=service_type.display_name if service_type else "Unknown",
                revealed_at=lead.revealed_at,
                is_contacted=lead.is_contacted,
                contacted_at=lead.contacted_at,
                notes=lead.notes,
            )
            for lead, service_type in leads_with_service_types
        ]
    )


@router.patch("/vendor/{lead_id}/mark-contacted")
async def mark_lead_as_contacted(
    lead_id: str,
    payload: MarkContactedRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Vendor marks lead as contacted
    """
    vendor_id = token.get("vendor_id")
    
    lead = await mark_lead_contacted(
        engine=engine,
        lead_id=lead_id,
        vendor_id=vendor_id,
        notes=payload.notes,
    )
    
    return success_response(
        message="Lead marked as contacted",
        data={
            "lead_id": str(lead.id),
            "is_contacted": lead.is_contacted,
            "contacted_at": lead.contacted_at,
            "notes": lead.notes,
        },
    )
