from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_service import VendorService
from core.enums import VendorStatus, DiscountType
from vendor.utils.pricing import calculate_final_price


async def create_base_service(engine: AIOEngine, vendor_id: str, payload):
    service = VendorService(
        vendor_id=vendor_id,
        location_id=payload.location_id,
        vertical_id=payload.vertical_id,
        name=payload.name,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        service_kind="BASE",
        included_service_ids=[],
        delivery_mode=payload.delivery_mode,
        dog_sizes=payload.dog_sizes or [],
        base_price=payload.base_price,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        images=payload.images or [],
    )

    await engine.save(service)
    
    return service


async def create_combo_service(engine: AIOEngine, vendor_id: str, payload):
    # Validate included services
    services = await engine.find(
        VendorService,
        VendorService.id.in_([ObjectId(sid) for sid in payload.included_service_ids])
    )

    if len(services) != len(payload.included_service_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more included services not found",
        )

    for svc in services:
        if svc.service_kind != "BASE":
            raise HTTPException(
                status_code=400,
                detail="Combo can include only BASE services",
            )
        if (
            svc.vendor_id != vendor_id
            or svc.location_id != payload.location_id
            or svc.vertical_id != payload.vertical_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Included services must match vendor, location and vertical",
            )

    combo = VendorService(
        vendor_id=vendor_id,
        location_id=payload.location_id,
        vertical_id=payload.vertical_id,
        name=payload.name,
        description=payload.description,
        service_kind="COMBO",
        included_service_ids=payload.included_service_ids,
        dog_sizes=payload.dog_sizes or [],
        base_price=payload.base_price,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        images=payload.images or [],
    )

    await engine.save(combo)
    
    return combo


async def list_services(
    engine: AIOEngine,
    vendor_id: str,
    location_id: str,
    vertical_id: str,
):
    return await engine.find(
        VendorService,
        (VendorService.vendor_id == vendor_id)
        & (VendorService.location_id == location_id)
        & (VendorService.vertical_id == vertical_id),
    )


async def mark_services_configured(engine: AIOEngine, vendor_id: str):
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    vendor.status = VendorStatus.SERVICES_CONFIGURED
    vendor.updated_at = datetime.utcnow()
    await engine.save(vendor)
    return vendor


async def update_service(
    engine,
    vendor_id: str,
    service_id: str,
    payload,
):
    service = await engine.find_one(
        VendorService,
        VendorService.id == ObjectId(service_id),
    )

    if not service or service.vendor_id != vendor_id:
        raise HTTPException(status_code=404, detail="Service not found")

    # Update service fields
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(service, field, value)

    service.updated_at = datetime.utcnow()
    await engine.save(service)
    
    return service

async def delete_service(
    engine: AIOEngine,
    vendor_id: str,
    service_id: str,
):
    service = await engine.find_one(
        VendorService,
        VendorService.id == ObjectId(service_id),
    )

    if not service or service.vendor_id != vendor_id:
        raise HTTPException(status_code=404, detail="Service not found")

    # Delete the service
    await engine.delete(service)

    return True
