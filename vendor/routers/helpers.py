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
from vendor.models.vendor_vertical import VendorVertical
from admin.models.vertical import Vertical
from bson import ObjectId
from vendor.services.availability_helper_service import get_daily_availability
from datetime import datetime

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
    Returns: [{ id, name, vertical_id, service_kind, price }]
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
            "vertical_id": svc.vertical_id,
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


@router.get("/my-verticals", response_model=dict)
async def get_my_verticals(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get verticals that THIS vendor has selected and offers
    Returns: [{ id, code, display_name, description, mode, is_active, images, url, icon }]
    """
    vendor_id = current_vendor["vendor_id"]
    
    # Get vendor's selected verticals
    vendor_verticals = await engine.find(
        VendorVertical,
        VendorVertical.vendor_id == vendor_id
    )
    
    if not vendor_verticals:
        return success_response(
            message="No verticals found",
            data={"verticals": []}
        ).model_dump()
    
    # Get vertical IDs
    vertical_ids = [ObjectId(vst.vertical_id) for vst in vendor_verticals]
    
    # Fetch full vertical details from admin
    verticals_data = await engine.find(
        Vertical,
        Vertical.id.in_(vertical_ids)
    )
    
    # Create a map for quick lookup
    vertical_map = {str(v.id): v for v in verticals_data}
    
    # Build response with vendor-specific data
    verticals_list = []
    
    for vst in vendor_verticals:
        v_def = vertical_map.get(vst.vertical_id)
        if v_def:
            verticals_list.append({
                "id": str(v_def.id),
                "vertical_id": str(vst.id),
                "code": v_def.code,
                "display_name": v_def.display_name,
                "description": v_def.description or "",
                "mode": v_def.mode.value if hasattr(v_def.mode, 'value') else v_def.mode,
                "is_active": vst.is_active,
                "images": build_image_list(v_def.image_blob_paths),
                "url": v_def.url or "",
                "icon": v_def.icon or "",
                "priority": v_def.priority
            })
            
    # Sort the list based on priority field
    verticals_list.sort(key=lambda x: x.get('priority', 100))
    
    return success_response(
        message="Verticals retrieved successfully",
        data={"verticals": verticals_list}
    ).model_dump()


@router.get("/verticals", response_model=dict)
async def get_all_verticals(
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get all available verticals (from admin) for vendor to choose from
    This is used during onboarding or when vendor wants to add new verticals
    Returns: [{ id, code, display_name, description, mode, images, url, icon }]
    """
    # Get all verticals from admin
    verticals_data = await engine.find(Vertical)
    
    verticals_list = []
    for v in verticals_data:
        verticals_list.append({
            "id": str(v.id),
            "code": v.code,
            "display_name": v.display_name,
            "description": v.description or "",
            "mode": v.mode.value if hasattr(v.mode, 'value') else v.mode,
            "images": build_image_list(v.image_blob_paths),
            "url": v.url or "",
            "icon": v.icon or "",
            "priority": v.priority,
            "is_active": v.is_active
        })
        
    # Sort the list based on priority field
    verticals_list.sort(key=lambda x: x.get('priority', 100))
    
    return success_response(
        message="Verticals retrieved successfully",
        data={"verticals": verticals_list}
    ).model_dump()
@router.get("/daily-availability", response_model=dict)
async def get_vendor_daily_availability(
    date: str, # YYYY-MM-DD
    location_id: str,
    vertical_id: str,
    care_professional_id: str = None,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get daily availability slots for a specific date
    """
    vendor_id = current_vendor["vendor_id"]
    
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return success_response(
            message="Invalid date format. Use YYYY-MM-DD",
            data={}
        ).model_dump()

    availability = await get_daily_availability(
        engine,
        vendor_id,
        target_date,
        location_id,
        vertical_id,
        care_professional_id
    )
    
    return success_response(
        message="Daily availability retrieved successfully",
        data=availability.model_dump()
    ).model_dump()
