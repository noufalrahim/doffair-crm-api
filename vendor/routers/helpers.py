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
from bson import ObjectId

router = APIRouter(
    prefix="/vendor/helpers",
    tags=["Vendor - Helpers"]
)



SERVICE_TYPE_METADATA = {
    "grooming": {"url": "/groom/overview", "icon": "/services/groom.png"},
    "vet": {"url": "/vet/overview", "icon": "/services/vet.png"},
    "boarding": {"url": "/boarding/overview", "icon": "/services/boarding.png"},
    "training": {"url": "/train/overview", "icon": "/services/train.png"},
    "shop": {"url": "/shop/overview", "icon": "/services/shop.png"},
    "walking": {"url": "/pet-walker/overview", "icon": "/services/walker.png"},
    "adoption": {"url": "/adoption/overview", "icon": "/services/adoption.png"},
    "daycare": {"url": "/daycare/overview", "icon": "/services/daycare.png"}, 
}


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
            "address": f"{loc.address_line_1}, {loc.city}, {loc.pincode}"
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


@router.get("/my-service-types", response_model=dict)
async def get_my_service_types(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get service types that THIS vendor has selected and offers
    Returns: [{ id, code, display_name, description, mode, is_active, images, url, icon }]
    """
    vendor_id = current_vendor["vendor_id"]
    
    # Get vendor's selected service types
    vendor_service_types = await engine.find(
        VendorServiceType,
        VendorServiceType.vendor_id == vendor_id
    )
    
    if not vendor_service_types:
        return success_response(
            message="No service types found",
            data={"service_types": []}
        ).model_dump()
    
    # Get service type IDs
    service_type_ids = [ObjectId(vst.service_type_id) for vst in vendor_service_types]
    
    # Fetch full service type details from admin
    service_types = await engine.find(
        ServiceType,
        ServiceType.id.in_(service_type_ids)
    )
    
    # Create a map for quick lookup
    service_type_map = {str(st.id): st for st in service_types}
    
    # Build response with vendor-specific data
    types_list = []
    
    # Always include Dashboard if requested, but usually this is a static frontend route. 
    # However, for the purpose of the sidebar menu which seems dynamically driven:
    # We might want to prepend 'Dashboard' manually if it's not in the DB types.
    # The user request implies they want these items to be available.
    # Since this endpoint returns "my-service-types", it implies configured services.
    # Dashboard is likely not a "service type" in the DB.
    # We will stick to enriching the DB items for now.
    
    for vst in vendor_service_types:
        st = service_type_map.get(vst.service_type_id)
        if st:
            metadata = SERVICE_TYPE_METADATA.get(st.code, {})
            types_list.append({
                "id": str(st.id),
                "service_type_id": str(vst.id),  # Vendor's VendorServiceType record ID
                "code": st.code,
                "display_name": st.display_name,
                "description": st.description or "",
                "mode": st.mode.value if hasattr(st.mode, 'value') else st.mode,
                "is_active": vst.is_active,  # Vendor's active status
                "images": build_image_list(st.image_blob_paths),
                "url": metadata.get("url", ""),
                "icon": metadata.get("icon", "")
            })
    
    return success_response(
        message="Service types retrieved successfully",
        data={"service_types": types_list}
    ).model_dump()


@router.get("/service-types", response_model=dict)
async def get_all_service_types(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get all available service types (from admin) for vendor to choose from
    This is used during onboarding or when vendor wants to add new service types
    Returns: [{ id, code, display_name, description, mode, images, url, icon }]
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
            "images": build_image_list(st.image_blob_paths),
            "url": SERVICE_TYPE_METADATA.get(st.code, {}).get("url", ""),
            "icon": SERVICE_TYPE_METADATA.get(st.code, {}).get("icon", "")
        }
        for st in service_types
    ]
    
    return success_response(
        message="Service types retrieved successfully",
        data={"service_types": types_list}
    ).model_dump()
