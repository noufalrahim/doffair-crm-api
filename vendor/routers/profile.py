"""
Vendor Profile Router - Get vendor information from token
"""
from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response, error_response
from vendor.models.vendor import Vendor
from bson import ObjectId

router = APIRouter(
    prefix="/vendor",
    tags=["Vendor - Profile"]
)


@router.get("/me", response_model=dict)
async def get_vendor_profile(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get current vendor's profile information from JWT token
    Returns complete vendor data
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        vendor = await engine.find_one(
            Vendor,
            Vendor.id == ObjectId(vendor_id)
        )
        
        if not vendor:
            return error_response(
                message="Vendor not found"
            ).model_dump()
        
        data = {
            "id": str(vendor.id),
            "legal_name": vendor.legal_name,
            "primary_contact_email": vendor.primary_contact_email,
            "primary_contact_phone": vendor.primary_contact_phone,
            "status": vendor.status.value if hasattr(vendor.status, 'value') else vendor.status,
            "is_active": vendor.is_active,
            "gst_number": vendor.gst_number,
            "business_registration_number": vendor.business_registration_number,
            "logo_blob_path": vendor.logo_blob_path,
            "profileImage": vendor.profileImage,
            "coverPhoto": vendor.coverPhoto,
            "gallery": vendor.gallery,
            "about": vendor.about,
            "alternative_phone": vendor.alternative_phone,
            "work_experience": vendor.work_experience,
            "home_service": vendor.home_service,
            "centre_service": vendor.centre_service,
            "home_service_radius": vendor.home_service_radius,
            "overall_rating": vendor.overall_rating,
            "created_at": vendor.created_at.isoformat() if vendor.created_at else None,
            "updated_at": vendor.updated_at.isoformat() if vendor.updated_at else None
        }

        care_professional_id = current_vendor.get("care_professional_id")
        if care_professional_id:
            from vendor.models.care_professional import CareProfessional
            from vendor.models.care_professional_permission import CareProfessionalPermission
            
            care_prof = await engine.find_one(
                CareProfessional,
                CareProfessional.id == ObjectId(care_professional_id)
            )
            
            permissions_doc = await engine.find_one(
                CareProfessionalPermission,
                CareProfessionalPermission.care_professional_id == care_professional_id
            )
            
            permissions = permissions_doc.permissions if permissions_doc else []
            
            if care_prof:
                care_prof_data = care_prof.model_dump()
                care_prof_data["id"] = str(care_prof.id)
                data["care_professional"] = care_prof_data
            else:
                data["care_professional"] = None
                
            data["permissions"] = permissions
            data["role"] = "care_professional"
        else:
            data["role"] = "vendor_admin"
            data["permissions"] = ["all"]

        return success_response(
            message="Vendor profile retrieved successfully",
            data=data
        ).model_dump()
        
    except Exception as e:
        return error_response(
            message=f"Failed to retrieve vendor profile: {str(e)}"
        ).model_dump()
