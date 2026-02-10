from odmantic import AIOEngine
from fastapi import HTTPException, status
from bson import ObjectId

from datetime import datetime
from admin.models.service_type import ServiceType
from admin.schemas.service_type import ServiceTypeCreate


async def create_service_type(
    engine: AIOEngine,
    payload: ServiceTypeCreate,
) -> ServiceType:
    # Check if ANY of the codes in the list already exist
    # Since 'code' is a list field in DB, we check if any exist in any document's code list.
    # $in operator checks if value exists in array field.
    # We want to know if *any* new code is already present.
    # Query: { "code": { "$in": payload.code } }
    
    existing = await engine.find_one(
        ServiceType,
        {"code": {"$in": payload.code}}
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more codes already exist in a service type",
        )

    service_type = ServiceType(
        code=payload.code,
        display_name=payload.display_name,
        description=payload.description,
        mode=payload.mode,
    )

    await engine.save(service_type)
    return service_type


async def list_service_types(
    engine: AIOEngine,
    include_inactive: bool = True,
) -> list[ServiceType]:
    if include_inactive:
        return await engine.find(ServiceType)
    return await engine.find(ServiceType, ServiceType.is_active == True)


async def toggle_service_type_status(
    engine: AIOEngine,
    service_type_id: str,
    is_active: bool,
) -> ServiceType:
    
    try:
        oid = ObjectId(service_type_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service type id format",
        )
    
    service_type = await engine.find_one(ServiceType, ServiceType.id == oid)
    if not service_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service type not found",
        )

    service_type.is_active = is_active
    service_type.updated_at = datetime.utcnow()
    await engine.save(service_type)
    return service_type
