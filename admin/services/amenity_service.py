from odmantic import AIOEngine
from datetime import datetime

from admin.models.amenity import Amenity
from admin.models.vertical_amenity import VerticalAmenity


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


async def map_amenities_to_vertical(
    engine: AIOEngine,
    vertical_id: str,
    amenity_codes: list[str],
):
    # Remove existing mappings
    await engine.remove(
        VerticalAmenity,
        VerticalAmenity.vertical_id == vertical_id,
    )

    mappings = [
        VerticalAmenity(
            vertical_id=vertical_id,
            amenity_code=code,
        )
        for code in amenity_codes
    ]

    for m in mappings:
        await engine.save(m)

    return mappings
