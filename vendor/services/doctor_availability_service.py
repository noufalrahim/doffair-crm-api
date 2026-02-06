from odmantic import AIOEngine
from vendor.models.doctor_availability import DoctorAvailability


async def add_doctor_availability(
    engine: AIOEngine,
    payload,
):
    availability = DoctorAvailability(
        service_type_id=payload.service_type_id,
        doctor_id=payload.doctor_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )

    await engine.save(availability)
    return availability
