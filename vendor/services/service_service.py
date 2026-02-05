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
        service_type_id=payload.service_type_id,
        name=payload.name,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        service_kind="BASE",
        included_service_ids=[],
        delivery_mode=payload.delivery_mode,

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
            or svc.service_type_id != payload.service_type_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Included services must match vendor, location and service type",
            )

    combo = VendorService(
        vendor_id=vendor_id,
        location_id=payload.location_id,
        service_type_id=payload.service_type_id,
        name=payload.name,
        description=payload.description,
        service_kind="COMBO",
        included_service_ids=payload.included_service_ids,
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
    service_type_id: str,
):
    # Fetch raw documents from MongoDB to bypass ODM validation issues with legacy data
    raw_services = await engine.get_collection(VendorService).find({
        "vendor_id": vendor_id,
        "location_id": location_id,
        "service_type_id": service_type_id
    }).to_list(length=None)
    
    # Use model_construct to create service objects without validation
    services = []
    for raw in raw_services:
        service = VendorService.model_construct(
            id=raw['_id'],
            vendor_id=raw.get('vendor_id'),
            service_type_id=raw.get('service_type_id'),
            location_id=raw.get('location_id'),
            name=raw.get('name'),
            service_kind=raw.get('service_kind'),
            image_blob_paths=raw.get('image_blob_paths', []),
            description=raw.get('description'),
            duration_minutes=raw.get('duration_minutes'),
            label=raw.get('label'),
            delivery_mode=raw.get('delivery_mode'),
            included_service_ids=raw.get('included_service_ids', []),
            is_active=raw.get('is_active', True),
            created_at=raw.get('created_at'),
            updated_at=raw.get('updated_at'),
        )
        services.append(service)
    
    return services


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
    # First check if service exists using raw MongoDB query to avoid ODM validation issues
    raw_service = await engine.get_collection(VendorService).find_one(
        {"_id": ObjectId(service_id), "vendor_id": vendor_id}
    )
    
    if not raw_service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Extract pricing fields from payload
    pricing_fields = {}
    service_fields = {}
    
    for field, value in payload.dict(exclude_unset=True).items():
        if field in ['base_price', 'discount_type', 'discount_value']:
            pricing_fields[field] = value
        else:
            service_fields[field] = value
    
    # Update service fields directly in MongoDB to avoid ODM validation on old data
    if service_fields:
        service_fields['updated_at'] = datetime.utcnow()
        await engine.get_collection(VendorService).update_one(
            {"_id": ObjectId(service_id)},
            {"$set": service_fields}
        )
    
    # Update pricing if pricing fields provided
    if pricing_fields:
        pricing_fields['updated_at'] = datetime.utcnow()
        result = await engine.get_collection(ServicePricing).update_one(
            {"service_id": service_id, "vendor_id": vendor_id},
            {"$set": pricing_fields}
        )
    
    # Fetch the updated service data from MongoDB
    updated_raw = await engine.get_collection(VendorService).find_one(
        {"_id": ObjectId(service_id)}
    )
    
    # Use model_construct to bypass validation (for legacy data with type issues)
    # This creates a model instance without validation
    service = VendorService.model_construct(
        _id=updated_raw['_id'],
        vendor_id=updated_raw.get('vendor_id'),
        service_type_id=updated_raw.get('service_type_id'),
        location_id=updated_raw.get('location_id'),
        name=updated_raw.get('name'),
        service_kind=updated_raw.get('service_kind'),
        image_blob_paths=updated_raw.get('image_blob_paths', []),
        description=updated_raw.get('description'),
        duration_minutes=updated_raw.get('duration_minutes'),
        label=updated_raw.get('label'),
        delivery_mode=updated_raw.get('delivery_mode'),
        included_service_ids=updated_raw.get('included_service_ids', []),
        is_active=updated_raw.get('is_active', True),
        created_at=updated_raw.get('created_at'),
        updated_at=updated_raw.get('updated_at'),
    )
    
    return service
