from odmantic import AIOEngine
from fastapi import HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from user.models.lead import Lead
from user.models.user import User
from vendor.models.vendor import Vendor
from admin.models.vertical import Vertical


DAILY_REVEAL_LIMIT = 5  # Maximum reveals per day per user


async def check_daily_limit(engine: AIOEngine, user_id: str) -> tuple[bool, int]:
    """
    Check if user has not exceeded daily reveal limit
    Returns: (can_reveal: bool, current_count: int)
    """
    # Get start and end of today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Count leads created today
    count = await engine.count(
        Lead,
        Lead.user_id == user_id,
        Lead.revealed_at >= today_start,
        Lead.revealed_at < today_end,
    )
    
    can_reveal = count < DAILY_REVEAL_LIMIT
    return can_reveal, count


async def check_duplicate_lead(
    engine: AIOEngine,
    user_id: str,
    vendor_id: str,
    vertical_id: str
) -> bool:
    """
    Check if lead already exists for this user-vendor-servicetype combination
    Returns True if duplicate exists
    """
    existing = await engine.find_one(
        Lead,
        (Lead.user_id == user_id) & (Lead.vendor_id == vendor_id) & (Lead.vertical_id == vertical_id),
    )
    return existing is not None


async def reveal_vendor_contact(
    engine: AIOEngine,
    user_id: str,
    vendor_id: str,
    vertical_id: str,
) -> tuple[Lead, Vertical]:
    """
    User reveals vendor contact - creates a lead
    """
    # 1. Check daily limit
    can_reveal, current_count = await check_daily_limit(engine, user_id)
    if not can_reveal:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached. You have already revealed {current_count} contacts today. Maximum is {DAILY_REVEAL_LIMIT} per day.",
        )
    
    # 2. Check for duplicate
    is_duplicate = await check_duplicate_lead(engine, user_id, vendor_id, vertical_id)
    if is_duplicate:
        # Return existing lead instead of creating new
        lead = await engine.find_one(
            Lead,
            (Lead.user_id == user_id) & (Lead.vendor_id == vendor_id) & (Lead.vertical_id == vertical_id),
        )
        vertical = await engine.find_one(
            Vertical,
            Vertical.id == ObjectId(vertical_id),
        )
        return lead, vertical
    
    # 3. Get user details
    user = await engine.find_one(User, User.id == ObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 4. Get vendor details
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.is_active:
        raise HTTPException(status_code=400, detail="Vendor is not active")
    
    # 5. Get vertical details
    vertical = await engine.find_one(
        Vertical,
        Vertical.id == ObjectId(vertical_id),
    )
    if not vertical:
        raise HTTPException(status_code=404, detail="Vertical not found")
    
    # Check if vertical is LEAD mode
    if vertical.mode != "lead":
        raise HTTPException(
            status_code=400,
            detail=f"This vertical is in {vertical.mode} mode, not LEAD mode. You cannot reveal contact for booking services.",
        )
    
    # 6. Create lead
    lead = Lead(
        user_id=user_id,
        vendor_id=vendor_id,
        vertical_id=vertical_id,
        user_name=user.name,
        user_phone=user.phone,
        user_email=user.email,
        vendor_name=vendor.legal_name or "Vendor",
        vendor_phone=vendor.primary_contact_phone,
        vendor_email=vendor.primary_contact_email,
    )
    
    await engine.save(lead)
    return lead, vertical


async def get_vendor_leads(
    engine: AIOEngine,
    vendor_id: str,
    limit: int = 50,
    skip: int = 0,
) -> list[tuple[Lead, Vertical]]:
    """
    Get all leads for a vendor with service type info
    """
    leads = await engine.find(
        Lead,
        Lead.vendor_id == vendor_id,
        sort=Lead.revealed_at.desc(),
        limit=limit,
        skip=skip,
    )
    
    # Fetch verticals
    result = []
    for lead in leads:
        vertical = await engine.find_one(
            Vertical,
            Vertical.id == ObjectId(lead.vertical_id),
        )
        result.append((lead, vertical))
    
    return result


async def mark_lead_contacted(
    engine: AIOEngine,
    lead_id: str,
    vendor_id: str,
    notes: str = None,
) -> Lead:
    """
    Vendor marks lead as contacted
    """
    lead = await engine.find_one(Lead, Lead.id == ObjectId(lead_id))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify vendor owns this lead
    if lead.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    lead.is_contacted = True
    lead.contacted_at = datetime.utcnow()
    if notes:
        lead.notes = notes
    lead.updated_at = datetime.utcnow()
    
    await engine.save(lead)
    return lead


async def get_user_leads(
    engine: AIOEngine,
    user_id: str,
    limit: int = 50,
    skip: int = 0,
) -> list[tuple[Lead, Vertical]]:
    """
    Get all leads created by a user
    """
    leads = await engine.find(
        Lead,
        Lead.user_id == user_id,
        sort=Lead.revealed_at.desc(),
        limit=limit,
        skip=skip,
    )
    
    # Fetch verticals
    result = []
    for lead in leads:
        vertical = await engine.find_one(
            Vertical,
            Vertical.id == ObjectId(lead.vertical_id),
        )
        result.append((lead, vertical))
    
    return result
