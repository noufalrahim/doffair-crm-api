from typing import Optional
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_user, require_vendor
from admin.models.vertical import Vertical
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
    UserSummary,
    PetSummary,
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
        id=str(booking.id),
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
        id=str(booking.id),
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
        id=str(booking.id),
        payment_id=str(payment.id),
        status=booking.status,
        message="Payment confirmed! Your booking is now pending vendor approval.",
    )


@router.get("/my-bookings")
async def get_my_bookings(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    User views all their bookings
    """
    user_id = token.get("user_id")
    
    bookings_with_payments, total = await get_user_bookings(engine, user_id, status_filter=status, limit=limit, skip=skip)
    
    return success_response(
        data={
            "data": [
                BookingResponse(
                    id=booking.get("id"),
                    vendor_name=booking.get("vendor_name"),
                    vendor_phone=booking.get("vendor_phone"),
                    service_name=booking.get("service_name"),
                    vertical_name=booking.get("vertical_name"),
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
                    user=UserSummary(
                        name=booking.get("user_name", "Unknown"),
                        phone=booking.get("user_phone", "Unknown"),
                        email=booking.get("user_email", "Unknown")
                    ),
                    pet=PetSummary(
                        name=booking.get("pet_name"),
                        type=booking.get("pet_type"),
                        breed=booking.get("pet_breed"),
                        age=booking.get("pet_age"),
                        weight=booking.get("pet_weight"),
                        gender=booking.get("pet_gender"),
                        medical_conditions=booking.get("pet_medical_conditions"),
                        special_notes=booking.get("pet_special_notes"),
                        images=booking.get("pet_images")
                    ) if booking.get("pet_name") else None
                ).model_dump(exclude_none=True)
                for booking, payment in bookings_with_payments
            ],
            "meta": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
    )


# ---------------------------------------------------------
# Vendor Endpoints - Approve/Reject Bookings
# ---------------------------------------------------------

@router.get("/vendor/my-bookings")
async def get_vendor_my_bookings(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    status: Optional[str] = Query(None, description="Filter by status: confirmed, pending, etc."),
    vertical_id: Optional[str] = Query(None, description="Filter by vertical ID"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    search: Optional[str] = Query(None, description="Search by customer name, phone, or email"),
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Vendor views all their bookings across primary and secondary databases
    """
    vendor_id = token.get("vendor_id")
    empty_result = {
        "data": [],
        "meta": {
            "total": 0,
            "skip": skip,
            "limit": limit,
        },
    }

    if not vertical_id:
        return success_response(data=empty_result)

    if not ObjectId.is_valid(vertical_id):
        return success_response(data=empty_result)

    vertical_obj_id = ObjectId(vertical_id)
    vertical = await engine.find_one(Vertical, Vertical.id == vertical_obj_id)
    if not vertical or not vertical.code:
        return success_response(data=empty_result)
    

    primary_status_filter = status.lower() if status else None
    bookings_with_payments, total = await get_vendor_bookings(
        engine,
        vendor_id,
        status_filter=primary_status_filter,
        limit=limit,
        skip=skip,
        is_offline=None,
        vertical_id=vertical_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        location_id=location_id
    )

    final_data = []
    for booking_dict, payment_dict in bookings_with_payments:
        final_data.append(
            BookingResponse(
                id=booking_dict["id"],
                vendor_name=booking_dict.get("vendor_name"),
                vendor_phone=booking_dict.get("vendor_phone"),
                service_name=booking_dict.get("service_name"),
                vertical_name=booking_dict.get("vertical_name"),
                booking_date=booking_dict.get("booking_date"),
                delivery_mode=booking_dict.get("delivery_mode"),
                service_address=booking_dict.get("service_address"),
                final_amount=booking_dict.get("final_amount"),
                status=booking_dict.get("status"),
                payment_status=payment_dict.get("status") if payment_dict else None,
                vendor_notes=booking_dict.get("vendor_notes"),
                rejection_reason=booking_dict.get("rejection_reason"),
                created_at=booking_dict.get("created_at"),
                approved_at=booking_dict.get("approved_at"),
                rejected_at=booking_dict.get("rejected_at"),
                user=UserSummary(
                    name=booking_dict.get("user_name", "Unknown"),
                    phone=booking_dict.get("user_phone", "Unknown"),
                    email=booking_dict.get("user_email", "Unknown")
                ),
                pet=PetSummary(
                    name=booking_dict.get("pet_name"),
                    type=booking_dict.get("pet_type"),
                    breed=booking_dict.get("pet_breed"),
                    age=booking_dict.get("pet_age"),
                    weight=booking_dict.get("pet_weight"),
                    gender=booking_dict.get("pet_gender"),
                    medical_conditions=booking_dict.get("pet_medical_conditions"),
                    special_notes=booking_dict.get("pet_special_notes"),
                    images=booking_dict.get("pet_images")
                ) if booking_dict.get("pet_name") else None
            ).model_dump(exclude_none=True)
        )
    return success_response(
        data={
            "data": final_data,
            "meta": {"total": total, "skip": skip, "limit": limit},
        }
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
        id=str(booking.id),
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
        id=str(booking.id),
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
    
    bookings_with_payments, total = await get_vendor_bookings(
        engine, vendor_id, status_filter=BookingStatus.PENDING_APPROVAL, limit=limit, skip=0
    )
    
    return success_response(
        data={
            "data": [
                BookingResponse(
                    id=booking.get("id"),
                    vendor_name=booking.get("vendor_name"),
                    vendor_phone=booking.get("vendor_phone"),
                    service_name=booking.get("service_name"),
                    vertical_name=booking.get("vertical_name"),
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
                    user=UserSummary(
                        name=booking.get("user_name", "Unknown"),
                        phone=booking.get("user_phone", "Unknown"),
                        email=booking.get("user_email", "Unknown")
                    ),
                    pet=PetSummary(
                        name=booking.get("pet_name"),
                        type=booking.get("pet_type"),
                        breed=booking.get("pet_breed"),
                        age=booking.get("pet_age"),
                        weight=booking.get("pet_weight"),
                        gender=booking.get("pet_gender"),
                        medical_conditions=booking.get("pet_medical_conditions"),
                        special_notes=booking.get("pet_special_notes"),
                        images=booking.get("pet_images")
                    ) if booking.get("pet_name") else None
                ).model_dump(exclude_none=True)
                for booking, payment in bookings_with_payments
            ],
            "meta": {
                "total": total,
                "skip": 0,
                "limit": limit
            }
        }
    )
