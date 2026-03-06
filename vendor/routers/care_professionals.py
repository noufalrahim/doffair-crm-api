from fastapi import APIRouter, Depends, Query
from typing import Optional
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.care_professional import (
    CareProfessionalCreateRequest,
    CareProfessionalUpdateRequest,
)
from vendor.services.care_professional_service import (
    create_care_professional,
    list_care_professionals,
    get_care_professional,
    update_care_professional,
    delete_care_professional,
)


router = APIRouter(
    prefix="/vendor/care-professionals",
    tags=["Vendor - Care Professionals"],
)


@router.post("")
async def add_care_professional(
    payload: CareProfessionalCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Create a care professional (also creates a user account with email, phone, password)"""
    vendor_id = token["vendor_id"]
    cp = await create_care_professional(engine, vendor_id, payload)

    return success_response(
        message="Care professional created",
        data={
            "id": str(cp.id),
            "user_id": cp.user_id,
            "name": cp.name,
            "role": cp.role,
            "location_id": cp.location_id,
            "vertical_id": cp.vertical_id,
            "is_active": cp.is_active,
            "specialization": cp.specialization,
            "years_of_experience": cp.years_of_experience,
            "consultation_fee": cp.consultation_fee,
            "license_number": cp.license_number,
            "profile_image": cp.profile_image,
        },
    )



from user.models.user import User
from vendor.models.vendor_location import VendorLocation
from vendor.schemas.care_professional import CareProfessionalResponse, UserResponse
from vendor.schemas.location import VendorLocationResponse
from bson import ObjectId

@router.get("")
async def get_care_professionals(
    vertical_id: Optional[str] = Query(None, alias="vertical_id"),
    location_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """List all care professionals for the vendor, optionally filter by location and role. vertical_id is required."""
    if not vertical_id:
        return success_response(
            data={
                "data": [],
                "meta": {
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "search": search,
                    "vertical_id": None,
                },
            }
        )

    vendor_id = token["vendor_id"]
    cps, total_count = await list_care_professionals(
        engine, vendor_id, location_id, role, skip, limit, search=search, vertical_id=vertical_id
    )

    # Bulk fetch related data
    user_ids = [ObjectId(cp.user_id) for cp in cps if cp.user_id]
    location_ids = [ObjectId(cp.location_id) for cp in cps if cp.location_id]

    users = await engine.find(User, User.id.in_(user_ids))
    locations = await engine.find(VendorLocation, VendorLocation.id.in_(location_ids))

    user_map = {str(u.id): u for u in users}
    location_map = {str(l.id): l for l in locations}

    response = []
    for cp in cps:
        user = user_map.get(cp.user_id)
        location = location_map.get(cp.location_id)

        user_info = None
        if user:
            user_info = UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                phone=user.phone,
                is_active=user.is_active,
                is_verified=user.is_verified
            )
        
        location_info = None
        if location:
            location_info = VendorLocationResponse(
                id=str(location.id),
                name=location.name,
                address_line_1=location.address_line_1,
                address_line_2=location.address_line_2,
                city=location.city,
                state=location.state,
                pincode=location.pincode,
                latitude=location.latitude,
                longitude=location.longitude,
                is_default=location.is_default
            )

        response.append(
            CareProfessionalResponse(
                id=str(cp.id),
                user_id=cp.user_id,
                name=cp.name,
                role=cp.role,
                location_id=cp.location_id,
                vertical_id=cp.vertical_id,
                is_active=cp.is_active,
                created_at=cp.created_at.isoformat(),
                specialization=cp.specialization,
                years_of_experience=cp.years_of_experience,
                consultation_fee=cp.consultation_fee,
                license_number=cp.license_number,
                profile_image=cp.profile_image,
                # Enriched objects
                user=user_info,
                location=location_info,
                # Legacy enriched fields
                email=user.email if user else None,
                phone=user.phone if user else None,
                location_name=location.name if location else None,
                location_address=f"{location.address_line_1}, {location.city}" if location else None,
            ).model_dump(mode='json')
        )

    return success_response(
        data={
            "data": response,
            "meta": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "search": search,
                "vertical_id": vertical_id,
            },
        }
    )


@router.get("/{care_professional_id}")
async def get_care_professional_by_id(
    care_professional_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Get a single care professional by ID"""
    vendor_id = token["vendor_id"]
    cp = await get_care_professional(engine, vendor_id, care_professional_id)

    # Fetch enrichment for single item too
    user = await engine.find_one(User, User.id == ObjectId(cp.user_id)) if cp.user_id else None
    location = await engine.find_one(VendorLocation, VendorLocation.id == ObjectId(cp.location_id)) if cp.location_id else None

    user_info = None
    if user:
        user_info = UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified
        )
    
    location_info = None
    if location:
        location_info = VendorLocationResponse(
            id=str(location.id),
            name=location.name,
            address_line_1=location.address_line_1,
            address_line_2=location.address_line_2,
            city=location.city,
            state=location.state,
            pincode=location.pincode,
            latitude=location.latitude,
            longitude=location.longitude,
            is_default=location.is_default
        )

    return success_response(
        data=CareProfessionalResponse(
            id=str(cp.id),
            user_id=cp.user_id,
            name=cp.name,
            role=cp.role,
            location_id=cp.location_id,
            vertical_id=cp.vertical_id,
            is_active=cp.is_active,
            specialization=cp.specialization,
            years_of_experience=cp.years_of_experience,
            consultation_fee=cp.consultation_fee,
            license_number=cp.license_number,
            profile_image=cp.profile_image,
            created_at=cp.created_at.isoformat(),
            # Enriched objects
            user=user_info,
            location=location_info,
            # Legacy fields
            email=user.email if user else None,
            phone=user.phone if user else None,
            location_name=location.name if location else None,
            location_address=f"{location.address_line_1}, {location.city}" if location else None,
        ).model_dump(mode='json')
    )


@router.patch("/{care_professional_id}")
async def update_care_professional_by_id(
    care_professional_id: str,
    payload: CareProfessionalUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Update a care professional. 
    Supported fields in payload: name, email, phone, location_id, role, is_active, specialization, years_of_experience, consultation_fee, license_number.
    """
    vendor_id = token["vendor_id"]
    cp = await update_care_professional(engine, vendor_id, care_professional_id, payload)
    
    # Fetch user for latest email/phone in response
    user = await engine.find_one(User, User.id == ObjectId(cp.user_id)) if cp.user_id else None

    return success_response(
        message="Care professional updated",
        data={
            "id": str(cp.id),
            "name": cp.name,
            "email": user.email if user else None,
            "phone": user.phone if user else None,
            "role": cp.role,
            "location_id": cp.location_id,
            "vertical_id": cp.vertical_id,
            "is_active": cp.is_active,
            "specialization": cp.specialization,
            "years_of_experience": cp.years_of_experience,
            "consultation_fee": cp.consultation_fee,
            "license_number": cp.license_number,
            "profile_image": cp.profile_image,
        },
    )


@router.delete("/{care_professional_id}")
async def delete_care_professional_by_id(
    care_professional_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Delete a care professional and their linked user account"""
    vendor_id = token["vendor_id"]
    cp = await delete_care_professional(engine, vendor_id, care_professional_id)

    return success_response(
        message="Care professional deleted",
        data={"id": str(cp.id)},
    )
