from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
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
    delete_service,
)
from vendor.utils.pricing import calculate_final_price

router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Services"],
)

# ---------------------------------------------------------
# Create BASE Service
# ---------------------------------------------------------

@router.post("/services/base")
async def add_base_service(
    payload: BaseServiceCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

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

@router.post("/services/combo")
async def add_combo_service(
    payload: ComboServiceCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

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

@router.get("/services")
async def get_services(
    location_id: str,
    vertical_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token.get("vendor_id")

    services = await list_services(
        engine,
        vendor_id,
        location_id,
        vertical_id,
    )

    return success_response(
        data=[
            VendorServiceResponse(
                id=str(s.id),
                name=s.name,
                service_kind=s.service_kind,
                location_id=s.location_id,
                vertical_id=s.vertical_id,
                label=s.label,
                images=s.images,
                is_active=s.is_active,
                description=s.description,
                duration_minutes=s.duration_minutes,
                delivery_mode=s.delivery_mode,
                dog_sizes=s.dog_sizes,
                base_price=s.base_price,
                discount_type=s.discount_type,
                discount_value=s.discount_value,
                final_price=calculate_final_price(
                    s.base_price,
                    s.discount_type,
                    s.discount_value
                ) if s.base_price is not None else None,
            )
            for s in services
        ]
    )


# ---------------------------------------------------------
# Update Vendor Service (PATCH)
# ---------------------------------------------------------

@router.patch("/services/{service_id}")
async def update_vendor_service(
    service_id: str,
    payload: VendorServiceUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    service = await update_service(engine, vendor_id, service_id, payload)
    
    return success_response(
        message="Service updated",
        data=VendorServiceResponse(
            id=str(service.id),
            name=service.name,
            service_kind=service.service_kind,
            location_id=service.location_id,
            vertical_id=service.vertical_id,
            label=service.label,
            images=service.images,
            is_active=service.is_active,
            description=service.description,
            duration_minutes=service.duration_minutes,
            delivery_mode=service.delivery_mode,
            dog_sizes=service.dog_sizes,
            base_price=service.base_price,
            discount_type=service.discount_type,
            discount_value=service.discount_value,
            final_price=calculate_final_price(
                service.base_price,
                service.discount_type,
                service.discount_value
            ) if service.base_price is not None else None,
        )
    )


# ---------------------------------------------------------
# Delete Vendor Service
# ---------------------------------------------------------

@router.delete("/services/{service_id}")
async def delete_vendor_service(
    service_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]
    await delete_service(engine, vendor_id, service_id)

    return success_response(message="Service deleted successfully")
