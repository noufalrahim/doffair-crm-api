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
from core.enums import CareProfessionalRole
from vendor.models.care_professional_permission import CareProfessionalPermission

ROLE_PERMISSIONS_MAP = {
    CareProfessionalRole.MANAGER: [
        "overview", "calendar", "bookings", "services", 
        "invoices", "availability", "staff", "ratings", "prescriptions"
    ],
    CareProfessionalRole.DOCTOR: [
        "overview", "calendar", "bookings", "availability", 
        "ratings", "prescriptions"
    ],
    CareProfessionalRole.STAFF: [
        "overview", "calendar", "bookings", "availability", "ratings"
    ],
    CareProfessionalRole.ADMIN: [
        "overview", "calendar", "bookings", "services", 
        "invoices", "availability", "staff", "ratings", "prescriptions"
    ],
}

async def assign_default_permissions(engine: AIOEngine, vendor_id: str, care_professional_id: str, role: CareProfessionalRole):
    permissions = ROLE_PERMISSIONS_MAP.get(role, [])
    
    perm_doc = await engine.find_one(
        CareProfessionalPermission,
        CareProfessionalPermission.care_professional_id == care_professional_id
    )
    
    if perm_doc:
        perm_doc.permissions = permissions
        perm_doc.updated_at = datetime.utcnow()
        await engine.save(perm_doc)
    else:
        perm_doc = CareProfessionalPermission(
            care_professional_id=care_professional_id,
            vendor_id=vendor_id,
            permissions=permissions
        )
        await engine.save(perm_doc)


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
        specialization=payload.specialization,
        years_of_experience=payload.years_of_experience,
        consultation_fee=payload.consultation_fee,
        license_number=payload.license_number,
        profile_image=payload.profile_image,
    )
    await engine.save(care_professional)
    
    # Assign default permissions
    await assign_default_permissions(engine, vendor_id, str(care_professional.id), care_professional.role)
    
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
        search_regex = {"$regex": search, "$options": "i"}
        user_criteria = {
            "$or": [
                {"name": search_regex},
                {"email": search_regex},
                {"phone": search_regex},
            ]
        }
        
        users = await engine.find(
            User,
            (User.name.match(search)) | (User.email.match(search)) | (User.phone.match(search))
        )
        user_ids = [str(u.id) for u in users]
        
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
    if not ObjectId.is_valid(care_professional_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid care professional ID",
        )

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
    user = await engine.find_one(User, User.id == ObjectId(cp.user_id))
    
    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle User updates (email, phone, name, password)
    if any(k in update_data for k in ["email", "phone", "name", "password"]) and user:
        if "email" in update_data:
            existing_email = await engine.find_one(User, (User.email == update_data["email"]) & (User.id != user.id))
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email {update_data['email']} already exists",
                )
            user.email = update_data["email"]

        if "phone" in update_data:
            existing_phone = await engine.find_one(User, (User.phone == update_data["phone"]) & (User.id != user.id))
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with phone {update_data['phone']} already exists",
                )
            user.phone = update_data["phone"]

        if "name" in update_data:
            user.name = update_data["name"]

        if "password" in update_data and update_data["password"]:
            user.password_hash = hash_password(update_data["password"])

        user.updated_at = datetime.utcnow()
        await engine.save(user)

    # Handle CareProfessional updates
    for field, value in update_data.items():
        if hasattr(cp, field):
            setattr(cp, field, value)

    # If role changed, update permissions
    if "role" in update_data:
        await assign_default_permissions(engine, vendor_id, str(cp.id), cp.role)

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
