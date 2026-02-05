from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from core.media import build_image_list
from utils.response import success_response

from vendor.schemas.service import (
    BaseServiceCreateRequest,
    ComboServiceCreateRequest,
    VendorServiceResponse,
    VendorServiceUpdateRequest,
)
from vendor.services.service_service import (
    create_base_service,
    create_combo_service,
    list_services,
    mark_services_configured,
    update_service,
)
from vendor.models.service_pricing import ServicePricing
from vendor.utils.pricing import calculate_final_price

router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Services"],
)

# ---------------------------------------------------------
# Create BASE Service
# ---------------------------------------------------------

@router.post("/{vendor_id}/services/base")
async def add_base_service(
    vendor_id: str,
    payload: BaseServiceCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = await create_base_service(engine, vendor_id, payload)
    await mark_services_configured(engine, vendor_id)

    return success_response(
        message="Base service created",
        data={
            "service_id": str(service.id),
            "service_kind": service.service_kind,
        },
    )


# ---------------------------------------------------------
# Create COMBO Service
# ---------------------------------------------------------

@router.post("/{vendor_id}/services/combo")
async def add_combo_service(
    vendor_id: str,
    payload: ComboServiceCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = await create_combo_service(engine, vendor_id, payload)
    await mark_services_configured(engine, vendor_id)

    return success_response(
        message="Combo service created",
        data={
            "service_id": str(service.id),
            "service_kind": service.service_kind,
        },
    )


# ---------------------------------------------------------
# Get Vendor Services (IMAGE-AWARE)
# ---------------------------------------------------------

@router.get("/{vendor_id}/services")
async def get_services(
    vendor_id: str,
    location_id: str,
    service_type_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token.get("vendor_id") != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    services = await list_services(
        engine,
        vendor_id,
        location_id,
        service_type_id,
    )
    
    # Fetch pricing for all services
    service_ids = [str(s.id) for s in services]
    pricings = await engine.find(
        ServicePricing,
        ServicePricing.service_id.in_(service_ids)
    )
    pricing_map = {p.service_id: p for p in pricings}

    return success_response(
        data=[
            VendorServiceResponse(
                id=str(s.id),
                name=s.name,
                service_kind=s.service_kind,
                location_id=s.location_id,
                service_type_id=s.service_type_id,
                label=s.label,
                images=build_image_list(s.image_blob_paths),
                is_active=s.is_active,
                base_price=pricing_map[str(s.id)].base_price if str(s.id) in pricing_map else None,
                discount_type=pricing_map[str(s.id)].discount_type if str(s.id) in pricing_map else None,
                discount_value=pricing_map[str(s.id)].discount_value if str(s.id) in pricing_map else None,
                final_price=calculate_final_price(
                    pricing_map[str(s.id)].base_price,
                    pricing_map[str(s.id)].discount_type,
                    pricing_map[str(s.id)].discount_value
                ) if str(s.id) in pricing_map else None,
            )
            for s in services
        ]
    )


# ---------------------------------------------------------
# Update Vendor Service (PATCH)
# ---------------------------------------------------------

@router.patch("/{vendor_id}/services/{service_id}")
async def update_vendor_service(
    vendor_id: str,
    service_id: str,
    payload: VendorServiceUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = await update_service(engine, vendor_id, service_id, payload)

    return success_response(
        message="Service updated",
        data={
            "service_id": str(service.id),
            "images": build_image_list(service.image_blob_paths),  # ✅ RETURN UPDATED IMAGES
        },
    )
