from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_admin
from utils.response import success_response
from schemas.common import APIResponse

from user.models.booking import Booking
from admin.schemas.booking import BookingSchema


router = APIRouter(
    prefix="/admin/bookings",
    tags=["Admin - Bookings"],
)


@router.get("/", response_model=APIResponse)
async def get_all_bookings(
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    bookings = await engine.find(
        Booking,
        sort=Booking.booking_date.desc(),
    )
    
    return success_response(
        data=[BookingSchema.model_validate(booking) for booking in bookings]
    ).model_dump()
