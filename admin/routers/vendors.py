from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine, get_secondary_motor_client
from core.config import settings
from core.security import require_admin
from utils.response import success_response

from admin.services.vendor_review import get_vendor_review_snapshot
from admin.services.vendor_approval import approve_vendor, reject_vendor
from schemas.common import APIResponse

from vendor.models.vendor import Vendor
from admin.schemas.vendor import VendorSchema
from admin.schemas.booking import BookingSchema

from bson import ObjectId
from datetime import datetime
from fastapi import Query


router = APIRouter(
    prefix="/admin/vendors",
    tags=["Admin - Vendors"],
)


@router.get("/bookings", response_model=APIResponse)
async def get_all_vendor_bookings(
    mode: str = Query(..., description="Mode must be 'online' or 'walkin'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    if mode not in ["online", "walkin"]:
        raise HTTPException(status_code=400, detail="mode must be 'online' or 'walkin'")
        
    if mode == "walkin":
        from user.models.booking import Booking
        total_count = await engine.count(Booking)
        bookings = await engine.find(
            Booking,
            sort=Booking.booking_date.desc(),
            skip=skip,
            limit=limit,
        )
        return success_response(
            data=[BookingSchema.model_validate(booking) for booking in bookings],
            meta={"total_count": total_count}
        ).model_dump()
        
    else:
        # online mode
        client = get_secondary_motor_client()
        db = client[settings.MONGODB_DB_NAME_SECONDARY]
        
        pri_client = engine.client
        pri_db = pri_client[settings.MONGODB_DB_NAME]
        
        total_count = await db.bookings.count_documents({})
        cursor = db.bookings.find({}).sort("createdAt", -1).skip(skip).limit(limit)
        
        formatted_bookings = []
        user_cache = {}
        vendor_cache = {}
        
        async for doc in cursor:
            # --- Resolve User Info ---
            user_id_raw = doc.get("userId")
            u_key = str(user_id_raw)
            
            user_name = "Unknown User"
            user_data = user_cache.get(u_key)
            
            if user_data:
                user_name = user_data["name"]
            elif user_id_raw:
                try:
                    u_oid = ObjectId(u_key) if isinstance(u_key, str) and len(u_key) == 24 else user_id_raw
                    # 1. Fetch from users collection for email/phone/username
                    u_doc = await db.users.find_one({"_id": u_oid})
                    # 2. Fetch from userInfo for real name
                    ui_doc = await db.userInfo.find_one({"userId": u_key}) or await db.userInfo.find_one({"userId": u_oid})
                    
                    if ui_doc:
                        user_name = ui_doc.get("name") or ui_doc.get("firstName") or ui_doc.get("fullName")
                    
                    if not user_name or user_name == "Unknown User":
                        if u_doc:
                            user_name = u_doc.get("username") or u_doc.get("name") or "Unknown User"
                    
                    if not user_name: user_name = "Unknown User"
                    
                    user_cache[u_key] = {"name": user_name}
                except Exception:
                    pass

            # --- Resolve Vendor Info ---
            vendor_id_raw = doc.get("serviceProviderId")
            sp_type = str(doc.get("serviceProviderType", "")).lower()
            v_key = str(vendor_id_raw)
            
            vendor_name = "Unknown Vendor"
            if v_key in vendor_cache:
                vendor_name = vendor_cache[v_key]
            elif vendor_id_raw:
                try:
                    v_oid = ObjectId(v_key) if isinstance(v_key, str) and len(v_key) == 24 else vendor_id_raw
                    
                    found_v = None
                    if sp_type == "groomer":
                        found_v = await db.groomerInfoNew.find_one({"_id": v_oid})
                        if not found_v: 
                            found_v = await pri_db.vendors.find_one({"_id": v_oid})
                    elif sp_type == "vet":
                        found_v = await db.vetInfo.find_one({"_id": v_oid})
                        if not found_v:
                            found_v = await db.groomerInfoNew.find_one({"_id": v_oid})
                        if not found_v:
                            found_v = await pri_db.vendors.find_one({"_id": v_oid})
                    else:
                        found_v = await pri_db.vendors.find_one({"_id": v_oid})
                    
                    if found_v:
                        vendor_name = found_v.get("name") or found_v.get("business_name") or found_v.get("businessName") or found_v.get("fullName") or "Unknown Vendor"
                    
                    vendor_cache[v_key] = vendor_name
                except Exception:
                    pass

            # --- Resolve Service Name ---
            service_name = "Unknown Service"
            if doc.get("services") and len(doc["services"]) > 0:
                s = doc["services"][0]
                if isinstance(s, dict):
                    service_name = s.get("name") or "Unknown Service"

            # --- Map Status ---
            status_str = doc.get("status", "pending")
            status_mapping = {
                "cancelByProvider": "cancelled",
                "cancelByUser": "cancelled",
                "confirmed": "confirmed",
                "completed": "completed",
                "pending": "pending_approval",
                "rejected": "rejected"
            }
            mapped_status = status_mapping.get(status_str, "pending_approval")
            
            booking_date = doc.get("startTime") or doc.get("createdAt")
            if not isinstance(booking_date, datetime):
                booking_date = datetime.utcnow()
                
            formatted_bookings.append({
                "id": str(doc["_id"]),
                "user_name": str(user_name),
                "vendor_name": str(vendor_name),
                "service_name": str(service_name),
                "booking_date": booking_date,
                "final_amount": float(doc.get("bookingAmount", 0.0) or 0.0),
                "status": mapped_status,
                "is_offline": False
            })
            
        return success_response(
            data=[BookingSchema(**b) for b in formatted_bookings],
            meta={"total_count": total_count}
        ).model_dump()



@router.get("/", response_model=APIResponse)
async def get_all_vendors(
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    vendors = await engine.find(Vendor)
    return success_response(
        data=[VendorSchema.model_validate(vendor) for vendor in vendors]
    ).model_dump()


@router.get("/{vendor_id}/review-snapshot", response_model=APIResponse)
async def vendor_review_snapshot(
    vendor_id: str,
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    try:
        snapshot = await get_vendor_review_snapshot(engine, vendor_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return success_response(data=snapshot).model_dump()


@router.post("/{vendor_id}/approve", response_model=APIResponse)
async def approve_vendor_api(
    vendor_id: str,
    engine: AIOEngine = Depends(get_engine),
    token: dict = Depends(require_admin),
):
    try:
        vendor = await approve_vendor(engine, vendor_id, token["sub"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Vendor approved successfully",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
        },
    ).model_dump()


@router.post("/{vendor_id}/reject", response_model=APIResponse)
async def reject_vendor_api(
    vendor_id: str,
    reason: str,
    engine: AIOEngine = Depends(get_engine),
    token: dict = Depends(require_admin),
):
    try:
        vendor = await reject_vendor(engine, vendor_id, token["sub"], reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        message="Vendor rejected",
        data={
            "vendor_id": vendor_id,
            "status": vendor.status,
            "reason": reason,
        },
    ).model_dump()