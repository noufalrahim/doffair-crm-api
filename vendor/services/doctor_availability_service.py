from odmantic import AIOEngine
from vendor.models.doctor_availability import DoctorAvailability


async def add_doctor_availability(
    engine: AIOEngine,
    payload: list,
):
    import asyncio

    availabilities = [
        DoctorAvailability(
            service_type_id=p.service_type_id,
            doctor_id=p.doctor_id,
            day_of_week=p.day_of_week,
            start_time=p.start_time,
            end_time=p.end_time,
        )
        for p in payload
    ]

    await asyncio.gather(*[engine.save(a) for a in availabilities])
    return availabilities
