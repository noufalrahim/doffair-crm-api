"""
Offline booking service - Using extended Booking model
Simple and working - no ODMantic bugs
"""
from datetime import datetime
from typing import Optional
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status

from user.models.booking import Booking
from core.enums import BookingStatus
import logging

logger = logging.getLogger(__name__)


async def create_offline_booking_simple(
    engine: AIOEngine,
    vendor_id: str,
    # Customer info
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str],
    customer_age: int,
    customer_gender: Optional[str],
    customer_address: Optional[str],
    customer_city: Optional[str],
    customer_pincode: Optional[str],
    customer_blood_group: Optional[str],
    customer_allergies: Optional[str],
    customer_medical_conditions: Optional[str],
    customer_notes: Optional[str],
    # Service info
    service_id: str,
    vertical_id: str,
    location_id: str,
    service_name: str,
    vertical_name: str,
    # Booking details
    booking_date: datetime,
    delivery_mode: str,
    service_address: Optional[str],
    service_city: Optional[str],
    service_pincode: Optional[str],
    final_amount: float,
    payment_mode: str,
    vendor_notes: Optional[str]
) -> Booking:
    """
    Create offline booking using Booking model
    Customer data stored as embedded fields
    """
    try:
        # Get vendor details (simplified - in production fetch from DB)
        vendor_name = "Vendor"  # TODO: Fetch actual vendor name
        vendor_phone = "1234567890"
        vendor_email = "vendor@example.com"
        
        # Create booking with offline flag
        booking = Booking(
            # Use phone as user_id for offline customers
            user_id=f"offline_{customer_phone}",
            vendor_id=vendor_id,
            service_id=service_id,
            vertical_id=vertical_id,
            location_id=location_id,
            
            # Customer details (cached in booking)
            user_name=customer_name,
            user_phone=customer_phone,
            user_email=customer_email or "",
            
            # Vendor details
            vendor_name=vendor_name,
            vendor_phone=vendor_phone,
            vendor_email=vendor_email,
            
            # Service details
            service_name=service_name,
            vertical_name=vertical_name,
            
            # Booking details
            booking_date=booking_date,
            delivery_mode=delivery_mode,
            service_address=service_address,
            service_city=service_city,
            service_pincode=service_pincode,
            
            # Pricing
            base_amount=final_amount,
            discount_amount=0.0,
            final_amount=final_amount,
            
            # Status - offline bookings are confirmed immediately
            status=BookingStatus.CONFIRMED,
            payment_id=None,
            
            # Vendor notes
            vendor_notes=vendor_notes,
            
            # Offline booking fields
            is_offline=True,
            customer_age=customer_age,
            customer_gender=customer_gender,
            customer_address_full=customer_address,
            customer_city_stored=customer_city,
            customer_pincode_stored=customer_pincode,
            customer_blood_group=customer_blood_group,
            customer_allergies=customer_allergies,
            customer_medical_conditions=customer_medical_conditions,
            customer_notes=customer_notes,
            payment_mode=payment_mode
        )
        
        await engine.save(booking)
        logger.info(f"✅ Offline booking created: {booking.id} for {customer_name}")
        
        return booking
        
    except Exception as e:
        logger.error(f"❌ Failed to create offline booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create offline booking: {str(e)}"
        )


async def get_offline_booking(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str
) -> Booking:
    """Get offline booking by ID"""
    try:
        booking_oid = ObjectId(booking_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format"
        )
    
    booking = await engine.find_one(
        Booking,
        (Booking.id == booking_oid) & 
        (Booking.vendor_id == vendor_id) &
        (Booking.is_offline == True)
    )
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offline booking not found"
        )
    
    return booking


async def list_offline_bookings(
    engine: AIOEngine,
    vendor_id: str,
    customer_phone: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20
) -> list[Booking]:
    """List offline bookings with filters"""
    try:
        query_conditions = [
            Booking.vendor_id == vendor_id,
            Booking.is_offline == True
        ]
        
        if customer_phone:
            query_conditions.append(Booking.user_phone == customer_phone)
        
        if from_date:
            query_conditions.append(Booking.booking_date >= from_date)
        
        if to_date:
            query_conditions.append(Booking.booking_date <= to_date)
        
        # Combine conditions
        final_query = query_conditions[0]
        for condition in query_conditions[1:]:
            final_query = final_query & condition
        
        bookings = await engine.find(
            Booking,
            final_query,
            skip=skip,
            limit=limit,
            sort=Booking.booking_date.desc()
        )
        
        return list(bookings)
        
    except Exception as e:
        logger.error(f"❌ Failed to list offline bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list offline bookings: {str(e)}"
        )


async def get_customer_history(
    engine: AIOEngine,
    vendor_id: str,
    customer_phone: str
) -> dict:
    """Get customer history via their phone number"""
    try:
        # Get all bookings for this phone
        bookings = await engine.find(
            Booking,
            (Booking.vendor_id == vendor_id) &
            (Booking.user_phone == customer_phone) &
            (Booking.is_offline == True),
            sort=Booking.booking_date.desc()
        )
        
        bookings_list = list(bookings)
        
        if not bookings_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No customer found with this phone"
            )
        
        # Get latest booking for customer info
        latest = bookings_list[0]
        
        total_spent = sum(b.final_amount for b in bookings_list)
        completed = [b for b in bookings_list if b.completed_at]
        
        return {
            "customer": {
                "name": latest.user_name,
                "phone": latest.user_phone,
                "email": latest.user_email,
                "age": latest.customer_age,
                "gender": latest.customer_gender,
                "blood_group": latest.customer_blood_group,
                "allergies": latest.customer_allergies,
                "medical_conditions": latest.customer_medical_conditions
            },
            "bookings": {
                "total": len(bookings_list),
                "completed": len(completed),
                "total_spent": total_spent,
                "last_visit": latest.booking_date.isoformat()
            },
            "history": [
                {
                    "booking_id": str(b.id),
                    "service_name": b.service_name,
                    "booking_date": b.booking_date.isoformat(),
                    "amount": b.final_amount,
                    "status": b.status.value if hasattr(b.status, 'value') else b.status,
                    "notes": b.vendor_notes
                }
                for b in bookings_list
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get customer history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer history: {str(e)}"
        )
