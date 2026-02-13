from datetime import datetime
from bson import ObjectId
from odmantic import AIOEngine
from fastapi import HTTPException, status

from vendor.models.vendor import Vendor
from vendor.models.vendor_service import VendorService
from vendor.models.service_pricing import ServicePricing
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

    )

    await engine.save(service)
    
    # Create pricing for this service
    pricing = ServicePricing(
        vendor_id=vendor_id,
        service_id=str(service.id),
        location_id=payload.location_id,
        base_price=payload.base_price,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
    )
    await engine.save(pricing)
    
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
    )

    await engine.save(combo)
    
    # Create pricing for this combo service
    pricing = ServicePricing(
        vendor_id=vendor_id,
        service_id=str(combo.id),
        location_id=payload.location_id,
        base_price=payload.base_price,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
    )
    await engine.save(pricing)
    
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

    # Extract pricing fields from payload
    pricing_fields = {}
    service_fields = {}
    
    for field, value in payload.dict(exclude_unset=True).items():
        if field in ['base_price', 'discount_type', 'discount_value']:
            pricing_fields[field] = value
        else:
            service_fields[field] = value
    
    # Update service fields
    for field, value in service_fields.items():
        setattr(service, field, value)

    service.updated_at = datetime.utcnow()
    await engine.save(service)
    
    # Update pricing if pricing fields provided
    if pricing_fields:
        pricing = await engine.find_one(
            ServicePricing,
            (ServicePricing.service_id == service_id) & (ServicePricing.vendor_id == vendor_id)
        )
        
        if pricing:
            for field, value in pricing_fields.items():
                setattr(pricing, field, value)
            pricing.updated_at = datetime.utcnow()
            await engine.save(pricing)
        elif 'base_price' in pricing_fields:
            # Create new pricing if missing and base_price is available
            pricing = ServicePricing(
                vendor_id=vendor_id,
                service_id=service_id,
                location_id=service.location_id,
                **pricing_fields
            )
            await engine.save(pricing)
        else:
            # Pricing missing and no base_price provided to create it
            # For now, we'll skip but this might need a warning or error in the future
            pass
    
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

    # Delete associated pricing
    pricing = await engine.find_one(
        ServicePricing,
        (ServicePricing.service_id == service_id) & (ServicePricing.vendor_id == vendor_id)
    )
    if pricing:
        await engine.delete(pricing)

    return True
