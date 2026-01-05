from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RevealMobileRequest(BaseModel):
    """
    User clicks 'Reveal Mobile Number' button on vendor profile
    """
    vendor_id: str
    service_type_id: str


class RevealMobileResponse(BaseModel):
    """
    Response after revealing mobile - shows vendor contact info
    """
    lead_id: str
    vendor_name: str
    vendor_phone: str
    vendor_email: str
    service_type_name: str
    message: str


class LeadResponse(BaseModel):
    """
    Single lead response for vendor dashboard
    """
    lead_id: str
    user_name: str
    user_phone: str
    user_email: str
    service_type_name: str
    revealed_at: datetime
    is_contacted: bool
    contacted_at: Optional[datetime]
    notes: Optional[str]


class MarkContactedRequest(BaseModel):
    """
    Vendor marks lead as contacted
    """
    notes: Optional[str] = None
