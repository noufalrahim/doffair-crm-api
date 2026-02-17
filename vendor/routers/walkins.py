from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine
from datetime import datetime
from bson import ObjectId
import logging

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response
from user.models.booking import Booking
from vendor.schemas.walkin import WalkinBookingCreate
from core.enums import BookingStatus, ServiceDeliveryMode
from vendor.models.vendor_service import VendorService
from admin.models.vertical import Vertical

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vendor/walkins",
    tags=["Vendor - Walk-in Bookings"]
)

@router.post("", response_model=dict)
async def create_walkin_booking(
    walkin_data: WalkinBookingCreate,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Create a new walk-in booking and store it in the primary database.
    """
    vendor_id = token.get("vendor_id")
    
    try:
        # Fetch vendor details to populate mandatory fields
        from vendor.models.vendor import Vendor
        vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
        
        # Determine Service Details
        bk_service_name = ", ".join(walkin_data.services)
        bk_vertical_name = "Walk-in"
        bk_service_id = None
        
        if walkin_data.service_id:
            bk_service_id = walkin_data.service_id
            # Fetch Service
            try:
                vs = await engine.find_one(VendorService, VendorService.id == ObjectId(bk_service_id))
                if vs:
                    bk_service_name = vs.name
                    # Fetch Type
                    st = await engine.find_one(Vertical, Vertical.id == ObjectId(vs.vertical_id))
                    if st:
                        bk_vertical_name = st.name
            except Exception as e:
                logger.error(f"Error fetching service details for walkin: {e}")
        
        # Use provided name if explicitly sent and lookup failed or not requested (though ID logic takes precedence)
        if not bk_service_id and walkin_data.service_name:
             bk_service_name = walkin_data.service_name

        # Create booking object
        booking = Booking(
            user_id=f"walkin_{walkin_data.customer_phone}",
            vendor_id=vendor_id,
            
            # Customer details
            user_name=walkin_data.customer_name,
            user_phone=walkin_data.customer_phone,
            user_email=walkin_data.customer_email,
            
            # Vendor details (fetched from DB)
            vendor_name=vendor.legal_name if vendor else "Walk-in Vendor",
            vendor_phone=vendor.primary_contact_phone if vendor else "",
            vendor_email=vendor.primary_contact_email if vendor else "",
            
            # Pet details (now optional)
            pet_name=walkin_data.pet_name,
            pet_type=None,
            pet_breed=walkin_data.pet_breed,
            pet_age=walkin_data.pet_age,
            pet_weight=walkin_data.pet_weight,
            pet_gender=walkin_data.pet_gender,
            pet_height=walkin_data.pet_height,
            pet_vaccinated=walkin_data.pet_vaccinated,
            pet_about=walkin_data.pet_about,
            
            # Booking details
            service_id=bk_service_id,
            service_name=bk_service_name,
            vertical_name=bk_vertical_name,
            delivery_mode=ServiceDeliveryMode.CENTER,
            booking_date=walkin_data.booking_date,
            
            # Pricing
            base_amount=walkin_data.final_amount,
            final_amount=walkin_data.final_amount,
            
            # Status
            status=walkin_data.status,
            
            # Walk-in specific fields (reusing offline fields)
            is_offline=True,
            vendor_notes=walkin_data.pet_about,
            
            # Additional notes
            customer_notes=f"Vaccinated: {walkin_data.pet_vaccinated}. Height: {walkin_data.pet_height}. About: {walkin_data.pet_about}"
        )

        
        await engine.save(booking)
        logger.info(f"✅ Walk-in booking created: {booking.id}")
        
        return success_response(
            message="Walk-in booking created successfully",
            data={"id": str(booking.id)}
        ).model_dump()
        
    except Exception as e:
        logger.error(f"❌ Failed to create walk-in booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create walk-in booking: {str(e)}")
