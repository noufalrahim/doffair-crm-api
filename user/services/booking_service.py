from odmantic import AIOEngine
from fastapi import HTTPException
from datetime import datetime
from bson import ObjectId
from typing import Optional

from user.models.booking import Booking
from user.models.payment import Payment
from user.models.user import User
from vendor.models.vendor import Vendor
from vendor.models.vendor_service import VendorService
from vendor.models.service_pricing import ServicePricing
from admin.models.vertical import Vertical
from vendor.models.vendor_location import VendorLocation
from core.enums import BookingStatus, PaymentStatus


async def create_booking(
    engine: AIOEngine,
    user_id: str,
    service_id: str,
    booking_date: datetime,
    delivery_mode: str,
    service_address: str = None,
    service_city: str = None,
    service_pincode: str = None,
    pet_name: str = None,
    pet_type: str = None,
    pet_breed: str = None,
    pet_age: int = None,
    pet_weight: float = None,
    pet_gender: str = None,
    pet_medical_conditions: str = None,
    pet_special_notes: str = None,
    pet_images: list[str] = None,
) -> Booking:
    """
    User creates a booking for a service
    Status: PENDING_PAYMENT
    """
    # 1. Get user details
    user = await engine.find_one(User, User.id == ObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Get service details
    service = await engine.find_one(VendorService, VendorService.id == ObjectId(service_id))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # 3. Get vendor details
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(service.vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    if not vendor.is_active:
        raise HTTPException(status_code=400, detail="Vendor is not active")
    
    # 4. Get vertical
    vertical = await engine.find_one(Vertical, Vertical.id == ObjectId(service.vertical_id))
    if not vertical:
        raise HTTPException(status_code=404, detail="Vertical not found")
    
    # Check if vertical is BOOKING mode
    if vertical.mode != "booking":
        raise HTTPException(
            status_code=400,
            detail=f"This vertical is in {vertical.mode} mode. Only 'booking' mode services can be booked.",
        )
    
    # 5. Get pricing
    pricing = await engine.find_one(
        ServicePricing,
        (ServicePricing.service_id == service_id) & (ServicePricing.location_id == service.location_id),
    )
    if not pricing:
        raise HTTPException(status_code=404, detail="Pricing not found for this service")
    
    # 6. Validate delivery mode
    from core.enums import ServiceDeliveryMode
    if delivery_mode not in [ServiceDeliveryMode.CENTER, ServiceDeliveryMode.HOME, ServiceDeliveryMode.BOTH]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid delivery_mode. Must be {ServiceDeliveryMode.CENTER}, {ServiceDeliveryMode.HOME}, or {ServiceDeliveryMode.BOTH}"
        )
    
    # Check if service supports this delivery mode
    from core.enums import ServiceDeliveryMode
    if service.delivery_mode == ServiceDeliveryMode.CENTER and delivery_mode == ServiceDeliveryMode.HOME:
        raise HTTPException(status_code=400, detail=f"This service is only available {ServiceDeliveryMode.CENTER}")
    elif service.delivery_mode == ServiceDeliveryMode.HOME and delivery_mode == ServiceDeliveryMode.CENTER:
        raise HTTPException(status_code=400, detail=f"This service is only available {ServiceDeliveryMode.HOME}")
    
    # 7. Validate address for HOME delivery
    from core.enums import ServiceDeliveryMode
    if delivery_mode == ServiceDeliveryMode.HOME or delivery_mode == ServiceDeliveryMode.BOTH:
        if not service_address or not service_city or not service_pincode:
            raise HTTPException(
                status_code=400,
                detail="service_address, service_city, and service_pincode are required for HOME delivery",
            )
    
    # 8. Calculate final amount
    base_amount = pricing.base_price
    discount_amount = 0.0
    
    if pricing.discount_type == "FLAT":
        discount_amount = pricing.discount_value or 0.0
    elif pricing.discount_type == "PERCENT":
        discount_amount = (base_amount * (pricing.discount_value or 0.0)) / 100
    
    final_amount = base_amount - discount_amount
    
    # 9. Create booking
    booking = Booking(
        user_id=user_id,
        vendor_id=service.vendor_id,
        service_id=service_id,
        vertical_id=service.vertical_id,
        location_id=service.location_id,
        user_name=user.name,
        user_phone=user.phone,
        user_email=user.email,
        vendor_name=vendor.legal_name or "Vendor",
        vendor_phone=vendor.primary_contact_phone,
        vendor_email=vendor.primary_contact_email,
        service_name=service.name,
        vertical_name=vertical.display_name,
        booking_date=booking_date,
        delivery_mode=delivery_mode,
        service_address=service_address,
        service_city=service_city,
        service_pincode=service_pincode,
        base_amount=base_amount,
        discount_amount=discount_amount,
        final_amount=final_amount,
        status=BookingStatus.PENDING_PAYMENT,
        pet_name=pet_name,
        pet_type=pet_type,
        pet_breed=pet_breed,
        pet_age=pet_age,
        pet_weight=pet_weight,
        pet_gender=pet_gender,
        pet_medical_conditions=pet_medical_conditions,
        pet_special_notes=pet_special_notes,
        pet_images=pet_images or [],
    )
    
    await engine.save(booking)
    return booking


async def initiate_payment(
    engine: AIOEngine,
    user_id: str,
    booking_id: str,
    payment_method: str = "razorpay",
) -> tuple[Booking, Payment]:
    """
    Initiate payment for a booking
    Returns: (booking, payment)
    """
    # 1. Get booking
    booking = await engine.find_one(Booking, Booking.id == ObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # 2. Verify user owns this booking
    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Check booking status
    if booking.status != BookingStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail=f"Cannot initiate payment. Booking status is {booking.status}")
    
    # 4. Create payment record
    # In real app, you'd call Razorpay API here to create order
    # For now, we'll just create a mock order_id
    import secrets
    mock_order_id = f"order_{secrets.token_hex(12)}"
    
    payment = Payment(
        booking_id=booking_id,
        user_id=user_id,
        vendor_id=booking.vendor_id,
        amount=booking.final_amount,
        payment_method=payment_method,
        payment_gateway_order_id=mock_order_id,
        status=PaymentStatus.PENDING,
    )
    
    await engine.save(payment)
    
    # 5. Update booking with payment_id
    booking.payment_id = str(payment.id)
    booking.updated_at = datetime.utcnow()
    await engine.save(booking)
    
    return booking, payment


async def confirm_payment(
    engine: AIOEngine,
    user_id: str,
    booking_id: str,
    payment_id: str,
    payment_gateway_payment_id: str,
    payment_gateway_signature: str,
) -> tuple[Booking, Payment]:
    """
    Confirm payment was successful
    Updates booking status to PENDING_APPROVAL
    """
    # 1. Get payment
    payment = await engine.find_one(Payment, Payment.id == ObjectId(payment_id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # 2. Verify user owns this payment
    if payment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Get booking
    booking = await engine.find_one(Booking, Booking.id == ObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # 4. Verify payment belongs to this booking
    if payment.booking_id != booking_id:
        raise HTTPException(status_code=400, detail="Payment does not belong to this booking")
    
    # 5. In real app, verify payment with Razorpay using signature
    # For now, we'll just mark it as successful
    
    # 6. Update payment - use MongoDB update and manually update the object
    now = datetime.utcnow()
    await engine.get_collection(Payment).update_one(
        {"_id": payment.id},
        {
            "$set": {
                "payment_gateway_payment_id": payment_gateway_payment_id,
                "payment_gateway_signature": payment_gateway_signature,
                "status": PaymentStatus.SUCCESS.value,
                "paid_at": now,
                "updated_at": now
            }
        }
    )
    
    # Manually update payment object fields (avoid re-fetching to bypass validation)
    payment.payment_gateway_payment_id = payment_gateway_payment_id
    payment.payment_gateway_signature = payment_gateway_signature
    payment.status = PaymentStatus.SUCCESS
    
    # 7. Update booking status to PENDING_APPROVAL
    await engine.get_collection(Booking).update_one(
        {"_id": booking.id},
        {
            "$set": {
                "status": BookingStatus.PENDING_APPROVAL.value,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Manually update booking object
    booking.status = BookingStatus.PENDING_APPROVAL
    
    return booking, payment


async def get_user_bookings(
    engine: AIOEngine,
    user_id: str,
    status_filter: str = None,
    limit: int = 50,
    skip: int = 0,
) -> tuple[list[tuple[dict, dict]], int]:
    """
    Get all bookings for a user with payment info
    Returns (bookings_list, total_count)
    """
    query = {"user_id": user_id}
    if status_filter:
        query["status"] = status_filter
        
    # Get total count
    total = await engine.get_collection(Booking).count_documents(query)

    # Fetch bookings
    booking_docs = await engine.get_collection(Booking).find(
        query
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for booking_doc in booking_docs:
        payment_data = None
        if booking_doc.get("payment_id"):
            payment_doc = await engine.get_collection(Payment).find_one({"_id": ObjectId(booking_doc.get("payment_id"))})
            if payment_doc:
                payment_data = {
                    "id": str(payment_doc["_id"]),
                    "booking_id": payment_doc.get("booking_id"),
                    "amount": payment_doc.get("amount"),
                    "status": payment_doc.get("status"),
                    "payment_method": payment_doc.get("payment_method"),
                    "payment_gateway_order_id": payment_doc.get("payment_gateway_order_id"),
                    "payment_gateway_payment_id": payment_doc.get("payment_gateway_payment_id"),
                }
        
        booking_data = {
            "id": str(booking_doc["_id"]),
            "user_id": booking_doc.get("user_id"),
            "vendor_id": booking_doc.get("vendor_id"),
            "service_id": booking_doc.get("service_id"),
            "user_name": booking_doc.get("user_name"),
            "user_phone": booking_doc.get("user_phone"),
            "user_email": booking_doc.get("user_email"),
            "vendor_name": booking_doc.get("vendor_name"),
            "vendor_phone": booking_doc.get("vendor_phone"),
            "service_name": booking_doc.get("service_name"),
            "vertical_name": booking_doc.get("vertical_name"),
            "booking_date": booking_doc.get("booking_date"),
            "delivery_mode": booking_doc.get("delivery_mode"),
            "service_address": booking_doc.get("service_address"),
            "final_amount": booking_doc.get("final_amount"),
            "status": booking_doc.get("status"),
            "vendor_notes": booking_doc.get("vendor_notes"),
            "rejection_reason": booking_doc.get("rejection_reason"),
            "created_at": booking_doc.get("created_at"),
            "approved_at": booking_doc.get("approved_at"),
            "rejected_at": booking_doc.get("rejected_at"),
            "payment_id": booking_doc.get("payment_id"),
            # Pet details
            "pet_name": booking_doc.get("pet_name"),
            "pet_type": booking_doc.get("pet_type"),
            "pet_breed": booking_doc.get("pet_breed"),
            "pet_age": booking_doc.get("pet_age"),
            "pet_weight": booking_doc.get("pet_weight"),
            "pet_gender": booking_doc.get("pet_gender"),
            "pet_medical_conditions": booking_doc.get("pet_medical_conditions"),
            "pet_special_notes": booking_doc.get("pet_special_notes"),
            "pet_images": booking_doc.get("pet_images", []),
        }
        result.append((booking_data, payment_data))
    
    return result, total


async def get_vendor_bookings(
    engine: AIOEngine,
    vendor_id: str,
    status_filter: str = None,
    limit: int = 50,
    skip: int = 0,
    is_offline: Optional[bool] = None,
    vertical_id: str = None,
) -> tuple[list[tuple[dict, dict]], int]:
    """
    Get all bookings for a vendor
    Returns (bookings_list, total_count)
    """
    query = {"vendor_id": vendor_id}
    if status_filter:
        query["status"] = status_filter
    
    if is_offline is not None:
        query["is_offline"] = is_offline
    
    if vertical_id:
        query["vertical_id"] = vertical_id
    
    # Get total count
    total = await engine.get_collection(Booking).count_documents(query)
    
    # Fetch bookings
    booking_docs = await engine.get_collection(Booking).find(
        query
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for booking_doc in booking_docs:
        payment_data = None
        if booking_doc.get("payment_id"):
            payment_doc = await engine.get_collection(Payment).find_one({"_id": ObjectId(booking_doc.get("payment_id"))})
            if payment_doc:
                payment_data = {
                    "id": str(payment_doc["_id"]),
                    "booking_id": payment_doc.get("booking_id"),
                    "amount": payment_doc.get("amount"),
                    "status": payment_doc.get("status"),
                    "payment_method": payment_doc.get("payment_method"),
                    "payment_gateway_order_id": payment_doc.get("payment_gateway_order_id"),
                    "payment_gateway_payment_id": payment_doc.get("payment_gateway_payment_id"),
                }
        
        booking_data = {
            "id": str(booking_doc["_id"]),
            "user_id": booking_doc.get("user_id"),
            "vendor_id": booking_doc.get("vendor_id"),
            "service_id": booking_doc.get("service_id"),
            "user_name": booking_doc.get("user_name"),
            "user_phone": booking_doc.get("user_phone"),
            "user_email": booking_doc.get("user_email"),
            "vendor_name": booking_doc.get("vendor_name"),
            "vendor_phone": booking_doc.get("vendor_phone"),
            "service_name": booking_doc.get("service_name"),
            "vertical_name": booking_doc.get("vertical_name"),
            "booking_date": booking_doc.get("booking_date"),
            "delivery_mode": booking_doc.get("delivery_mode"),
            "service_address": booking_doc.get("service_address"),
            "final_amount": booking_doc.get("final_amount"),
            "status": booking_doc.get("status"),
            "vendor_notes": booking_doc.get("vendor_notes"),
            "rejection_reason": booking_doc.get("rejection_reason"),
            "created_at": booking_doc.get("created_at"),
            "approved_at": booking_doc.get("approved_at"),
            "rejected_at": booking_doc.get("rejected_at"),
            "payment_id": booking_doc.get("payment_id"),
            # Pet details
            "pet_name": booking_doc.get("pet_name"),
            "pet_type": booking_doc.get("pet_type"),
            "pet_breed": booking_doc.get("pet_breed"),
            "pet_age": booking_doc.get("pet_age"),
            "pet_weight": booking_doc.get("pet_weight"),
            "pet_gender": booking_doc.get("pet_gender"),
            "pet_medical_conditions": booking_doc.get("pet_medical_conditions"),
            "pet_special_notes": booking_doc.get("pet_special_notes"),
            "pet_images": booking_doc.get("pet_images", []),
        }
        result.append((booking_data, payment_data))
    
    return result, total


async def approve_booking(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str,
    notes: str = None,
) -> Booking:
    """
    Vendor approves a booking
    """
    # 1. Get booking
    booking = await engine.find_one(Booking, Booking.id == ObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # 2. Verify vendor owns this booking
    if booking.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Check if booking can be approved
    if booking.status != BookingStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve booking with status {booking.status}. Must be PENDING_APPROVAL.",
        )
    

    now = datetime.utcnow()
    update_fields = {
        "status": BookingStatus.CONFIRMED.value,
        "approved_at": now,
        "updated_at": now
    }
    if notes:
        update_fields["vendor_notes"] = notes
    
    await engine.get_collection(Booking).update_one(
        {"_id": booking.id},
        {"$set": update_fields}
    )
    
    # Manually update booking object
    booking.status = BookingStatus.CONFIRMED
    if notes:
        booking.vendor_notes = notes
    
    return booking


async def reject_booking(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str,
    rejection_reason: str,
) -> tuple[Booking, Payment]:
    """
    Vendor rejects a booking
    Initiates refund
    """
    # 1. Get booking
    booking = await engine.find_one(Booking, Booking.id == ObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # 2. Verify vendor owns this booking
    if booking.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 3. Check if booking can be rejected
    if booking.status != BookingStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject booking with status {booking.status}. Must be PENDING_APPROVAL.",
        )
    
    # 4. Get payment data from MongoDB directly to bypass validation
    payment_data = None
    if booking.payment_id:
        payment_doc = await engine.get_collection(Payment).find_one({"_id": ObjectId(booking.payment_id)})
        if payment_doc and payment_doc.get("status") == PaymentStatus.SUCCESS.value:
            # 5. Initiate refund - update MongoDB directly
            # In real app, call Razorpay refund API here
            now = datetime.utcnow()
            await engine.get_collection(Payment).update_one(
                {"_id": ObjectId(booking.payment_id)},
                {
                    "$set": {
                        "status": PaymentStatus.REFUNDED.value,
                        "refunded_at": now,
                        "refund_amount": payment_doc.get("amount"),
                        "refund_reason": rejection_reason,
                        "updated_at": now
                    }
                }
            )
            payment_data = {
                "id": str(payment_doc["_id"]),
                "status": PaymentStatus.REFUNDED.value,
                "amount": payment_doc.get("amount"),
                "refund_amount": payment_doc.get("amount"),
            }
    
    # 6. Update booking 
    now = datetime.utcnow()
    await engine.get_collection(Booking).update_one(
        {"_id": booking.id},
        {
            "$set": {
                "status": BookingStatus.REJECTED.value,
                "rejected_at": now,
                "rejection_reason": rejection_reason,
                "updated_at": now
            }
        }
    )
    
    # Manually update booking object
    booking.status = BookingStatus.REJECTED
    booking.rejection_reason = rejection_reason
    
    return booking, payment_data
