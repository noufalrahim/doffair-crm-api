from odmantic import AIOEngine
from fastapi import HTTPException, status
from datetime import datetime
from bson import ObjectId

from vendor.models.care_professional import CareProfessional
from user.models.user import User
from vendor.schemas.care_professional import (
    CareProfessionalCreateRequest,
    CareProfessionalUpdateRequest,
)
from admin.utils.password import hash_password


async def create_care_professional(
    engine: AIOEngine,
    vendor_id: str,
    payload: CareProfessionalCreateRequest,
) -> CareProfessional:
    # Check if email/phone already exist in users collection
    existing_email = await engine.find_one(User, User.email == payload.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {payload.email} already exists",
        )

    existing_phone = await engine.find_one(User, User.phone == payload.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with phone {payload.phone} already exists",
        )

    # Create user record with credentials
    user = User(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    await engine.save(user)

    # Create care professional linked to user
    care_professional = CareProfessional(
        vendor_id=vendor_id,
        user_id=str(user.id),
        location_id=payload.location_id,
        vertical_id=payload.vertical_id,
        name=payload.name,
        role=payload.role,
    )
    await engine.save(care_professional)
    return care_professional



async def list_care_professionals(
    engine: AIOEngine,
    vendor_id: str,
    location_id: str = None,
    role: str = None,
    skip: int = 0,
    limit: int = 10,
    search: str = None,
    vertical_id: str = None,
):
    filters = [CareProfessional.vendor_id == vendor_id]
    
    if location_id:
        filters.append(CareProfessional.location_id == location_id)
        
    if role:
        filters.append(CareProfessional.role == role)

    if vertical_id:
        filters.append(CareProfessional.vertical_id == vertical_id)
        
    if search:
        # Search Users first
        # We need to find users whose name, email or phone matches the search string (case insensitive ideally, but strict here for now or use regex)
        # Odmantic doesn't support $regex easily directly in find without raw query or compatible operator
        # Let's use regex for partial match
        search_regex = {"$regex": search, "$options": "i"}
        user_criteria = {
            "$or": [
                {"name": search_regex},
                {"email": search_regex},
                {"phone": search_regex},
            ]
        }
        # We need raw query support or find all users then filter CPs. 
        # Since we can't easily do raw query with engine.find(User, ...), let's use the underlying collection or simple find.
        # Wait, engine.find accepts ODMantic query expressions. 
        # To do OR across fields in ODMantic: (User.name.match(regex)) | ...
        
        # NOTE: ODMantic match() uses regex potentially. Let's try to construct the query.
        # But wait, User.name is Optional[str].
        
        # Alternative: fetch all users linked to this vendor's CPs? No, too many.
        # Better: Search users globally matching the term.
        # It might return users not belonging to this vendor, but the CP filter (vendor_id) will filter those out.
        
        users = await engine.find(
            User,
            (User.name.match(search)) | (User.email.match(search)) | (User.phone.match(search))
        )
        user_ids = [str(u.id) for u in users]
        
        # Now filter CPs: Matches CP Name OR CP User ID is in found_user_ids
        # CP.name.match(search) | CP.user_id.in_(user_ids)
        
        if user_ids:
            filters.append(
                (CareProfessional.name.match(search)) | (CareProfessional.user_id.in_(user_ids))
            )
        else:
            filters.append(CareProfessional.name.match(search))

    total_count = await engine.count(CareProfessional, *filters)
    care_professionals = await engine.find(
        CareProfessional,
        *filters,
        skip=skip,
        limit=limit,
        sort=CareProfessional.created_at.desc(),
    )
    return care_professionals, total_count


async def get_care_professional(
    engine: AIOEngine,
    vendor_id: str,
    care_professional_id: str,
) -> CareProfessional:
    cp = await engine.find_one(
        CareProfessional,
        CareProfessional.id == ObjectId(care_professional_id),
        CareProfessional.vendor_id == vendor_id,
    )
    if not cp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care professional not found",
        )
    return cp


async def update_care_professional(
    engine: AIOEngine,
    vendor_id: str,
    care_professional_id: str,
    payload: CareProfessionalUpdateRequest,
) -> CareProfessional:
    cp = await get_care_professional(engine, vendor_id, care_professional_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cp, field, value)

    cp.updated_at = datetime.utcnow()
    await engine.save(cp)
    return cp


async def delete_care_professional(
    engine: AIOEngine,
    vendor_id: str,
    care_professional_id: str,
):
    cp = await get_care_professional(engine, vendor_id, care_professional_id)

    # Also delete the linked user record
    if cp.user_id:
        user = await engine.find_one(User, User.id == ObjectId(cp.user_id))
        if user:
            await engine.delete(user)

    await engine.delete(cp)
    return cp
