from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, BeforeValidator, computed_field
from core.enums import BookingStatus

PyObjectId = Annotated[str, BeforeValidator(str)]


class BookingSchema(BaseModel):
    id: PyObjectId
    user_name: str
    vendor_name: Optional[str] = None
    service_name: str
    booking_date: datetime
    final_amount: float
    status: BookingStatus
    is_offline: bool = False
    
    @computed_field
    def booking_type(self) -> str:
        return "Offline/Walk-in" if self.is_offline else "Online"

    class Config:
        from_attributes = True
