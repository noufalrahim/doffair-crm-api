"""
Offline booking router - Simplified working version
Uses extended Booking model
"""
from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine
from typing import Optional
from datetime import datetime

from core.database import get_engine
from core.security import get_current_vendor
from vendor.schemas.offline_booking_v2 import (
    CreateOfflineBookingSimple,
    OfflineBookingResponse
)
from vendor.services.offline_booking_service_v2 import (
    create_offline_booking_simple,
    get_offline_booking,
    list_offline_bookings,
    get_customer_history
)
from utils.response import success_response

router = APIRouter(
    prefix="/vendor/offline-bookings",
    tags=["Vendor - Offline Bookings (Working)"]
)


@router.post("", response_model=dict)
async def create_offline_booking_endpoint(
    payload: CreateOfflineBookingSimple,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Create offline booking - customer data embedded in booking
    NO ODMANTIC BUGS - Uses working Booking model
    """
    vendor_id = current_vendor["vendor_id"]
    
    booking = await create_offline_booking_simple(
        engine=engine,
        vendor_id=vendor_id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=payload.customer_email,
        customer_age=payload.customer_age,
        customer_gender=payload.customer_gender,
        customer_address=payload.customer_address,
        customer_city=payload.customer_city,
        customer_pincode=payload.customer_pincode,
        customer_blood_group=payload.customer_blood_group,
        customer_allergies=payload.customer_allergies,
        customer_medical_conditions=payload.customer_medical_conditions,
        customer_notes=payload.customer_notes,
        service_id=payload.service_id,
        vertical_id=payload.vertical_id,
        location_id=payload.location_id,
        service_name=payload.service_name,
        vertical_name=payload.vertical_name,
        booking_date=payload.booking_date,
        delivery_mode=payload.delivery_mode,
        service_address=payload.service_address,
        service_city=payload.service_city,
        service_pincode=payload.service_pincode,
        final_amount=payload.final_amount,
        payment_mode=payload.payment_mode,
        vendor_notes=payload.vendor_notes
    )
    
    response_data = OfflineBookingResponse(
        id=str(booking.id),
        vendor_id=booking.vendor_id,
        customer_name=booking.user_name,
        customer_phone=booking.user_phone,
        customer_email=booking.user_email or None,
        customer_age=booking.customer_age,
        customer_gender=booking.customer_gender,
        service_name=booking.service_name,
        vertical_name=booking.vertical_name,
        booking_date=booking.booking_date,
        delivery_mode=booking.delivery_mode,
        final_amount=booking.final_amount,
        payment_mode=booking.payment_mode,
        status=booking.status.value if hasattr(booking.status, 'value') else booking.status,
        vendor_notes=booking.vendor_notes,
        created_at=booking.created_at
    )
    
    return success_response(
        message="Offline booking created successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.get("/{booking_id}", response_model=dict)
async def get_offline_booking_endpoint(
    booking_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """Get offline booking details"""
    vendor_id = current_vendor["vendor_id"]
    
    booking = await get_offline_booking(engine, vendor_id, booking_id)
    
    response_data = OfflineBookingResponse(
        id=str(booking.id),
        vendor_id=booking.vendor_id,
        customer_name=booking.user_name,
        customer_phone=booking.user_phone,
        customer_email=booking.user_email or None,
        customer_age=booking.customer_age,
        customer_gender=booking.customer_gender,
        service_name=booking.service_name,
        vertical_name=booking.vertical_name,
        booking_date=booking.booking_date,
        delivery_mode=booking.delivery_mode,
        final_amount=booking.final_amount,
        payment_mode=booking.payment_mode,
        status=booking.status.value if hasattr(booking.status, 'value') else booking.status,
        vendor_notes=booking.vendor_notes,
        created_at=booking.created_at
    )
    
    return success_response(
        message="Booking retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()


@router.get("", response_model=dict)
async def list_offline_bookings_endpoint(
    customer_phone: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """List offline bookings with filters"""
    vendor_id = current_vendor["vendor_id"]
    
    bookings = await list_offline_bookings(
        engine, vendor_id, customer_phone, from_date, to_date, skip, limit
    )
    
    booking_responses = [
        OfflineBookingResponse(
            id=str(b.id),
            vendor_id=b.vendor_id,
            customer_name=b.user_name,
            customer_phone=b.user_phone,
            customer_email=b.user_email or None,
            customer_age=b.customer_age,
            customer_gender=b.customer_gender,
            service_name=b.service_name,
            vertical_name=b.vertical_name,
            booking_date=b.booking_date,
            delivery_mode=b.delivery_mode,
            final_amount=b.final_amount,
            payment_mode=b.payment_mode,
            status=b.status.value if hasattr(b.status, 'value') else b.status,
            vendor_notes=b.vendor_notes,
            created_at=b.created_at
        ).model_dump()
        for b in bookings
    ]
    
    return success_response(
        message="Bookings retrieved successfully",
        data={
            "bookings": booking_responses,
            "total": len(booking_responses)
        }
    ).model_dump()


@router.get("/customer/{customer_phone}/history", response_model=dict)
async def get_customer_history_endpoint(
    customer_phone: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get complete customer history by phone number
    Includes all bookings and customer details
    """
    vendor_id = current_vendor["vendor_id"]
    
    history = await get_customer_history(engine, vendor_id, customer_phone)
    
    return success_response(
        message="Customer history retrieved successfully",
        data=history
    ).model_dump()
