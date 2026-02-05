from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_user, require_vendor
from utils.response import success_response
from user.schemas.booking import (
    CreateBookingRequest,
    CreateBookingResponse,
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    ConfirmPaymentRequest,
    ConfirmPaymentResponse,
    BookingResponse,
    ApproveBookingRequest,
    RejectBookingRequest,
    VendorActionResponse,
)
from user.services.booking_service import (
    create_booking,
    initiate_payment,
    confirm_payment,
    get_user_bookings,
    get_vendor_bookings,
    approve_booking,
    reject_booking,
)
from core.enums import BookingStatus


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


# ---------------------------------------------------------
# User Endpoints - Create & Manage Bookings
# ---------------------------------------------------------

@router.post("/create")
async def create_new_booking(
    payload: CreateBookingRequest,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    User creates a booking for a service
    Status: PENDING_PAYMENT
    """
    user_id = token.get("user_id")
    
    booking = await create_booking(
        engine=engine,
        user_id=user_id,
        service_id=payload.service_id,
        booking_date=payload.booking_date,
        delivery_mode=payload.delivery_mode,
        service_address=payload.service_address,
        service_city=payload.service_city,
        service_pincode=payload.service_pincode,
        pet_name=payload.pet_name,
        pet_type=payload.pet_type,
        pet_breed=payload.pet_breed,
        pet_age=payload.pet_age,
        pet_weight=payload.pet_weight,
        pet_gender=payload.pet_gender,
        pet_medical_conditions=payload.pet_medical_conditions,
        pet_special_notes=payload.pet_special_notes,
        pet_images=payload.pet_images,
    )
    
    return CreateBookingResponse(
        booking_id=str(booking.id),
        service_name=booking.service_name,
        vendor_name=booking.vendor_name,
        booking_date=booking.booking_date,
        final_amount=booking.final_amount,
        status=booking.status,
        payment_required=True,
        message="Booking created successfully. Please proceed with payment.",
    )


@router.post("/initiate-payment")
async def initiate_booking_payment(
    payload: InitiatePaymentRequest,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    User initiates payment for a booking
    Returns Razorpay order details
    """
    user_id = token.get("user_id")
    
    booking, payment = await initiate_payment(
        engine=engine,
        user_id=user_id,
        booking_id=payload.booking_id,
        payment_method=payload.payment_method,
    )
    
    return InitiatePaymentResponse(
        payment_id=str(payment.id),
        booking_id=str(booking.id),
        amount=payment.amount,
        currency="INR",
        payment_gateway_order_id=payment.payment_gateway_order_id,
        message="Payment initiated. Please complete payment on Razorpay.",
    )


@router.post("/confirm-payment")
async def confirm_booking_payment(
    payload: ConfirmPaymentRequest,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
):
    """
    User confirms payment was successful
    Updates booking status to PENDING_APPROVAL
    """
    user_id = token.get("user_id")
    
    booking, payment = await confirm_payment(
        engine=engine,
        user_id=user_id,
        booking_id=payload.booking_id,
        payment_id=payload.payment_id,
        payment_gateway_payment_id=payload.payment_gateway_payment_id,
        payment_gateway_signature=payload.payment_gateway_signature,
    )
    
    return ConfirmPaymentResponse(
        booking_id=str(booking.id),
        payment_id=str(payment.id),
        status=booking.status,
        message="Payment confirmed! Your booking is now pending vendor approval.",
    )


@router.get("/my-bookings")
async def get_my_bookings(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    User views all their bookings
    """
    user_id = token.get("user_id")
    
    bookings_with_payments = await get_user_bookings(engine, user_id, limit, skip)
    
    return success_response(
        data=[
            BookingResponse(
                booking_id=booking.get("id"),
                user_name=booking.get("user_name"),
                user_phone=booking.get("user_phone"),
                user_email=booking.get("user_email"),
                vendor_name=booking.get("vendor_name"),
                vendor_phone=booking.get("vendor_phone"),
                service_name=booking.get("service_name"),
                service_type_name=booking.get("service_type_name"),
                booking_date=booking.get("booking_date"),
                delivery_mode=booking.get("delivery_mode"),
                service_address=booking.get("service_address"),
                final_amount=booking.get("final_amount"),
                status=booking.get("status"),
                payment_status=payment.get("status") if payment else None,
                vendor_notes=booking.get("vendor_notes"),
                rejection_reason=booking.get("rejection_reason"),
                created_at=booking.get("created_at"),
                approved_at=booking.get("approved_at"),
                rejected_at=booking.get("rejected_at"),
                pet_name=booking.get("pet_name"),
                pet_type=booking.get("pet_type"),
                pet_breed=booking.get("pet_breed"),
                pet_age=booking.get("pet_age"),
                pet_weight=booking.get("pet_weight"),
                pet_gender=booking.get("pet_gender"),
                pet_medical_conditions=booking.get("pet_medical_conditions"),
                pet_special_notes=booking.get("pet_special_notes"),
                pet_images=booking.get("pet_images"),
            )
            for booking, payment in bookings_with_payments
        ]
    )


# ---------------------------------------------------------
# Vendor Endpoints - Approve/Reject Bookings
# ---------------------------------------------------------

@router.get("/vendor/my-bookings")
async def get_vendor_my_bookings(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    status: str = Query(None, description="Filter by status: PENDING_APPROVAL, CONFIRMED, etc."),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Vendor views all their bookings
    Can filter by status to see pending approvals
    """
    vendor_id = token.get("vendor_id")
    
    bookings_with_payments = await get_vendor_bookings(
        engine, vendor_id, status_filter=status, limit=limit, skip=skip
    )
    
    return success_response(
        data=[
            BookingResponse(
                booking_id=booking.get("id"),
                user_name=booking.get("user_name"),
                user_phone=booking.get("user_phone"),
                user_email=booking.get("user_email"),
                vendor_name=booking.get("vendor_name"),
                vendor_phone=booking.get("vendor_phone"),
                service_name=booking.get("service_name"),
                service_type_name=booking.get("service_type_name"),
                booking_date=booking.get("booking_date"),
                delivery_mode=booking.get("delivery_mode"),
                service_address=booking.get("service_address"),
                final_amount=booking.get("final_amount"),
                status=booking.get("status"),
                payment_status=payment.get("status") if payment else None,
                vendor_notes=booking.get("vendor_notes"),
                rejection_reason=booking.get("rejection_reason"),
                created_at=booking.get("created_at"),
                approved_at=booking.get("approved_at"),
                rejected_at=booking.get("rejected_at"),
                pet_name=booking.get("pet_name"),
                pet_type=booking.get("pet_type"),
                pet_breed=booking.get("pet_breed"),
                pet_age=booking.get("pet_age"),
                pet_weight=booking.get("pet_weight"),
                pet_gender=booking.get("pet_gender"),
                pet_medical_conditions=booking.get("pet_medical_conditions"),
                pet_special_notes=booking.get("pet_special_notes"),
                pet_images=booking.get("pet_images"),
            )
            for booking, payment in bookings_with_payments
        ]
    )


@router.post("/vendor/{booking_id}/approve")
async def vendor_approve_booking(
    booking_id: str,
    payload: ApproveBookingRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Vendor approves a booking
    Changes status to CONFIRMED
    """
    vendor_id = token.get("vendor_id")
    
    booking = await approve_booking(
        engine=engine,
        vendor_id=vendor_id,
        booking_id=booking_id,
        notes=payload.notes,
    )
    
    return VendorActionResponse(
        booking_id=str(booking.id),
        status=booking.status,
        message=f"Booking approved successfully! Service scheduled for {booking.booking_date.strftime('%Y-%m-%d %H:%M')}",
        refund_initiated=False,
    )


@router.post("/vendor/{booking_id}/reject")
async def vendor_reject_booking(
    booking_id: str,
    payload: RejectBookingRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Vendor rejects a booking
    Changes status to REJECTED
    Initiates refund automatically
    """
    vendor_id = token.get("vendor_id")
    
    booking, payment = await reject_booking(
        engine=engine,
        vendor_id=vendor_id,
        booking_id=booking_id,
        rejection_reason=payload.rejection_reason,
    )
    
    refund_initiated = payment and payment.get("status") == "REFUNDED"
    
    return VendorActionResponse(
        booking_id=str(booking.id),
        status=booking.status,
        message=f"Booking rejected. {('Refund has been initiated.' if refund_initiated else 'No refund needed.')}",
        refund_initiated=refund_initiated,
    )


@router.get("/vendor/pending-approvals")
async def get_pending_approvals(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Vendor views bookings pending approval
    Shortcut for GET /vendor/my-bookings?status=PENDING_APPROVAL
    """
    vendor_id = token.get("vendor_id")
    
    bookings_with_payments = await get_vendor_bookings(
        engine, vendor_id, status_filter=BookingStatus.PENDING_APPROVAL, limit=limit, skip=0
    )
    
    return success_response(
        data=[
            BookingResponse(
                booking_id=booking.get("id"),
                user_name=booking.get("user_name"),
                user_phone=booking.get("user_phone"),
                user_email=booking.get("user_email"),
                vendor_name=booking.get("vendor_name"),
                vendor_phone=booking.get("vendor_phone"),
                service_name=booking.get("service_name"),
                service_type_name=booking.get("service_type_name"),
                booking_date=booking.get("booking_date"),
                delivery_mode=booking.get("delivery_mode"),
                service_address=booking.get("service_address"),
                final_amount=booking.get("final_amount"),
                status=booking.get("status"),
                payment_status=payment.get("status") if payment else None,
                vendor_notes=booking.get("vendor_notes"),
                rejection_reason=booking.get("rejection_reason"),
                created_at=booking.get("created_at"),
                approved_at=booking.get("approved_at"),
                rejected_at=booking.get("rejected_at"),
                pet_name=booking.get("pet_name"),
                pet_type=booking.get("pet_type"),
                pet_breed=booking.get("pet_breed"),
                pet_age=booking.get("pet_age"),
                pet_weight=booking.get("pet_weight"),
                pet_gender=booking.get("pet_gender"),
                pet_medical_conditions=booking.get("pet_medical_conditions"),
                pet_special_notes=booking.get("pet_special_notes"),
                pet_images=booking.get("pet_images"),
            )
            for booking, payment in bookings_with_payments
        ]
    )
