from odmantic import AIOEngine
from datetime import datetime

from admin.models.amenity import Amenity
from admin.models.service_type_amenity import ServiceTypeAmenity


async def create_amenity(engine: AIOEngine, payload):
    amenity = Amenity(
        code=payload.code.upper(),
        display_name=payload.display_name,
        description=payload.description,
        icon=payload.icon,
    )
    await engine.save(amenity)
    return amenity


async def list_amenities(engine: AIOEngine):
    return await engine.find(Amenity, Amenity.is_active == True)


async def map_amenities_to_service_type(
    engine: AIOEngine,
    service_type_id: str,
    amenity_codes: list[str],
):
    # Remove existing mappings
    await engine.remove(
        ServiceTypeAmenity,
        ServiceTypeAmenity.service_type_id == service_type_id,
    )

    mappings = [
        ServiceTypeAmenity(
            service_type_id=service_type_id,
            amenity_code=code,
        )
        for code in amenity_codes
    ]

    for m in mappings:
        await engine.save(m)

    return mappings
