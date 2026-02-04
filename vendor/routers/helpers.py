"""
Helper endpoints for frontend - get dropdown data
"""
from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response
from core.media import build_image_list
from vendor.models.vendor_location import VendorLocation
from vendor.models.vendor_service import VendorService
from vendor.models.vendor_service_type import VendorServiceType
from admin.models.service_type import ServiceType

router = APIRouter(
    prefix="/vendor/helpers",
    tags=["Vendor - Helpers"]
)


@router.get("/locations", response_model=dict)
async def get_vendor_locations(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get all vendor locations for dropdown
    Returns: [{ id, name, address }]
    """
    vendor_id = current_vendor["vendor_id"]
    
    locations = await engine.find(
        VendorLocation,
        VendorLocation.vendor_id == vendor_id
    )
    
    locations_list = [
        {
            "id": str(loc.id),
            "name": loc.name,
            "address": f"{loc.address}, {loc.city}, {loc.pincode}"
        }
        for loc in locations
    ]
    
    return success_response(
        message="Locations retrieved successfully",
        data={"locations": locations_list}
    ).model_dump()


@router.get("/services", response_model=dict)
async def get_vendor_services(
    location_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get all services for a location
    Returns: [{ id, name, service_type_id, service_type_name, price }]
    """
    vendor_id = current_vendor["vendor_id"]
    
    services = await engine.find(
        VendorService,
        (VendorService.vendor_id == vendor_id) & 
        (VendorService.location_id == location_id)
    )
    
    services_list = [
        {
            "id": str(svc.id),
            "name": svc.name,
            "service_type_id": svc.service_type_id,
            "service_kind": svc.service_kind,
            "delivery_mode": svc.delivery_mode.value if hasattr(svc.delivery_mode, 'value') else svc.delivery_mode,
            "label": svc.label
        }
        for svc in services
    ]
    
    return success_response(
        message="Services retrieved successfully",
        data={"services": services_list}
    ).model_dump()


@router.get("/service-types", response_model=dict)
async def get_all_service_types(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get all available service types (from admin) for vendor to choose from
    This is used during onboarding or when vendor wants to add new service types
    Returns: [{ id, code, display_name, description, mode, images }]
    """
    # Get all active service types from admin
    service_types = await engine.find(
        ServiceType,
        ServiceType.is_active == True
    )
    
    types_list = [
        {
            "id": str(st.id),
            "code": st.code,
            "display_name": st.display_name,
            "description": st.description or "",
            "mode": st.mode.value if hasattr(st.mode, 'value') else st.mode,
            "images": build_image_list(st.image_blob_paths)
        }
        for st in service_types
    ]
    
    return success_response(
        message="Service types retrieved successfully",
        data={"service_types": types_list}
    ).model_dump()
