from typing import Optional
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine

from core.database import get_engine, get_secondary_engine
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
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    status: Optional[str] = Query(None, description="Filter by status: confirmed, pending, etc."),
    vertical_id: Optional[str] = Query(None, description="Filter by vertical ID"),
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
    
    # 1. Fetch from Primary DB (Modern + Offline)
    primary_status_filter = status.lower() if status else None
    primary_docs_tuples, _ = await get_vendor_bookings(
        engine, 
        vendor_id, 
        status_filter=primary_status_filter, 
        limit=1000, 
        skip=0, 
        is_offline=None, 
        vertical_id=vertical_id,
        search=search,
        start_date=start_date,
        end_date=end_date
    )
    
    unified_list = []
    for booking_dict, payment_dict in primary_docs_tuples:
        unified_list.append({
            "type": "primary",
            "booking": booking_dict,
            "payment": payment_dict,
            "sort_key": booking_dict.get("created_at") or datetime.min
        })

    # 2. Fetch from Secondary DB (Legacy)
    vertical_codes = []
    if vertical_id and ObjectId.is_valid(vertical_id):
         st = await engine.find_one(Vertical, Vertical.id == ObjectId(vertical_id))
         if st:
             vertical_codes = st.code
    
    if not vertical_id or vertical_codes:
        secondary_criteria = {
            "$or": [
                {"serviceProviderId": ObjectId(vendor_id)}, 
                {"serviceProviderId": vendor_id},           
                {"vendor_id": vendor_id}                    
            ]
        }
        
        if vertical_codes:
            secondary_criteria["serviceProviderType"] = {"$in": vertical_codes}
            
        if status:
            st_lower = status.lower()
            if st_lower == "confirmed":
                secondary_criteria["status"] = "confirmed"
            elif st_lower == "pending":
                secondary_criteria["status"] = {"$in": ["pending", "ongoing", "rescheduleRequest"]}
            elif st_lower == "cancelled":
                secondary_criteria["status"] = {"$in": ["cancelled", "cancelByProvider", "rejected"]}
            elif st_lower == "completed":
                secondary_criteria["status"] = "completed"
            else:
                secondary_criteria["status"] = st_lower
        
        if start_date or end_date:
            date_filter = {}
            if start_date: date_filter["$gte"] = start_date
            if end_date: date_filter["$lte"] = end_date
            secondary_criteria["startTime"] = date_filter
            
        if search:
            import re
            search_regex = {"$regex": re.escape(search), "$options": "i"}
            secondary_criteria["$or"] = [
                {"user_name": search_regex},
                {"user_phone": search_regex},
                {"user_email": search_regex},
                {"service_name": search_regex},
                {"instructions": search_regex},
                {"name": search_regex}
            ]

        secondary_coll = secondary_engine.database.get_collection("bookings")
        legacy_cursor = secondary_coll.find(secondary_criteria).sort("createdAt", -1).limit(1000)
        
        async for doc in legacy_cursor:
            unified_list.append({
                "type": "legacy",
                "raw_doc": doc,
                "sort_key": doc.get("createdAt") or doc.get("booking_date") or datetime.min
            })

    # 3. Sort and Paginate
    unified_list.sort(key=lambda x: x["sort_key"], reverse=True)
    total = len(unified_list)
    paginated = unified_list[skip : skip + limit]
    
    # 4. Final Mapping
    final_data = []
    for item in paginated:
        if item["type"] == "primary":
            b = item["booking"]
            p = item["payment"]
            final_data.append(
                BookingResponse(
                    id=b["id"],
                    vendor_name=b.get("vendor_name"),
                    vendor_phone=b.get("vendor_phone"),
                    service_name=b.get("service_name"),
                    vertical_name=b.get("vertical_name"),
                    booking_date=b.get("booking_date"),
                    delivery_mode=b.get("delivery_mode"),
                    service_address=b.get("service_address"),
                    final_amount=b.get("final_amount"),
                    status=b.get("status"),
                    payment_status=p.get("status") if p else None,
                    vendor_notes=b.get("vendor_notes"),
                    rejection_reason=b.get("rejection_reason"),
                    created_at=b.get("created_at"),
                    approved_at=b.get("approved_at"),
                    rejected_at=b.get("rejected_at"),
                    user=UserSummary(
                        name=b.get("user_name", "Unknown"),
                        phone=b.get("user_phone", "Unknown"),
                        email=b.get("user_email", "Unknown")
                    ),
                    pet=PetSummary(
                        name=b.get("pet_name"),
                        type=b.get("pet_type"),
                        breed=b.get("pet_breed"),
                        age=b.get("pet_age"),
                        weight=b.get("pet_weight"),
                        gender=b.get("pet_gender"),
                        medical_conditions=b.get("pet_medical_conditions"),
                        special_notes=b.get("pet_special_notes"),
                        images=b.get("pet_images")
                    ) if b.get("pet_name") else None
                ).model_dump(exclude_none=True)
            )
        else:
            doc = item["raw_doc"]
            # Minimal mapping for legacy
            u_name = doc.get("user_name") or "Unknown"
            u_phone = doc.get("user_phone") or "Unknown"
            u_email = doc.get("user_email") or "Unknown"
            
            # Try to fetch user details if missing from doc
            if u_name == "Unknown" and doc.get("userId"):
                try:
                    user_doc = await secondary_engine.database.get_collection("users").find_one({"_id": doc.get("userId")})
                    if user_doc:
                        u_name = user_doc.get("username", user_doc.get("firstName", "Unknown"))
                        u_phone = user_doc.get("phoneNumber", user_doc.get("phone", "Unknown"))
                        u_email = user_doc.get("email", "Unknown")
                except Exception: pass

            final_data.append(
                BookingResponse(
                    id=str(doc["_id"]),
                    vendor_name=None,
                    vendor_phone=None,
                    service_name=doc.get("service_name") or (doc.get("services", [{}])[0].get("name") if doc.get("services") else "Unknown"),
                    vertical_name=doc.get("serviceType", "Unknown"),
                    booking_date=doc.get("startTime") or doc.get("booking_date") or datetime.min,
                    delivery_mode="In-Center",
                    service_address=None,
                    final_amount=float(doc.get("bookingAmount", 0)),
                    status=doc.get("status", "confirmed").lower(),
                    payment_status=None,
                    vendor_notes=doc.get("instructions"),
                    created_at=item["sort_key"],
                    user=UserSummary(name=u_name, phone=u_phone, email=u_email),
                    pet=PetSummary(name=doc.get("pet_name")) if doc.get("pet_name") else None
                ).model_dump(exclude_none=True)
            )

    return success_response(
        data={
            "data": final_data,
            "meta": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
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
