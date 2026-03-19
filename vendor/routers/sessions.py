from fastapi import APIRouter, Depends, HTTPException, status
from odmantic import AIOEngine
from typing import List, Any, Dict

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response
from vendor.models.session import VendorSession
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/vendor/sessions",
    tags=["Vendor Sessions"]
)

class SessionResponse(BaseModel):
    id: str
    device_name: str
    device_type: str
    os: str
    browser: str
    ip_address: str
    last_active: datetime
    is_current: bool

@router.get("", response_model=Dict[str, Any])
async def list_active_sessions(
    current_vendor: Dict[str, Any] = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List all active sessions for the current vendor.
    """
    vendor_id = current_vendor["vendor_id"]
    current_jti = current_vendor["jti"]
    
    sessions = await engine.find(
        VendorSession,
        (VendorSession.vendor_id == vendor_id) & (VendorSession.is_active == True)
    )
    
    response_data = [
        SessionResponse(
            id=str(s.id),
            device_name=s.device_name or "Unknown Device",
            device_type=s.device_type or "Unknown",
            os=s.os or "Unknown",
            browser=s.browser or "Unknown",
            ip_address=s.ip_address or "Unknown",
            last_active=s.last_active,
            is_current=(s.jti == current_jti)
        ).model_dump()
        for s in sessions
    ]
    
    # Sort to show current session first, then by last active
    response_data.sort(key=lambda x: (not x["is_current"], x["last_active"]), reverse=True)
    
    return success_response(
        message="Sessions retrieved successfully",
        data=response_data
    ).model_dump()

@router.delete("/{session_id}", response_model=Dict[str, Any])
async def terminate_session(
    session_id: str,
    current_vendor: Dict[str, Any] = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Terminate a specific session.
    """
    vendor_id = current_vendor["vendor_id"]
    
    from bson import ObjectId
    try:
        oid = ObjectId(session_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
        
    session = await engine.find_one(
        VendorSession,
        (VendorSession.id == oid) & (VendorSession.vendor_id == vendor_id)
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_active = False
    await engine.save(session)
    
    return success_response(
        message="Session terminated successfully",
        data={"session_id": session_id}
    ).model_dump()
