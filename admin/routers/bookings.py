from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine
from core.database import get_engine, get_secondary_motor_client
from core.config import settings
from core.security import require_admin
from utils.response import success_response
from admin.schemas.booking import BookingSchema
from schemas.common import APIResponse
from bson import ObjectId
from datetime import datetime
from user.models.booking import Booking
from typing import Optional

router = APIRouter(
    prefix="/admin/bookings",
    tags=["Admin - Bookings"],
)

@router.get("/", response_model=APIResponse)
async def get_bookings(
    mode: str = Query("online", description="Mode must be 'online' or 'walkin'"),
    status: Optional[str] = Query(None),
    vendor_type: Optional[str] = Query(None, description="Filter by 'groomer' or 'vet'"),
    vendor_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    engine: AIOEngine = Depends(get_engine),
    _: dict = Depends(require_admin),
):
    if mode not in ["online", "walkin"]:
        raise HTTPException(status_code=400, detail="mode must be 'online' or 'walkin'")
        
    if mode == "walkin":
        query = {}
        if status:
            query["status"] = status
        
        if vendor_id:
            query["vendor_id"] = vendor_id
            
        if vendor_type:
            # Vertical name mapping
            vt_map = {
                "groomer": ["Grooming", "Pet Grooming"],
                "vet": ["Vet Clinic", "Veterinary"]
            }
            if vendor_type in vt_map:
                query["vertical_name"] = {"$in": vt_map[vendor_type]}
            
        total_count = await engine.count(Booking, **query)
        bookings = await engine.find(
            Booking,
            **query,
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
        
        filter_query = {}
        if status:
            # Map status if needed for online
            status_mapping_rev = {
                "cancelled": ["cancelByProvider", "cancelByUser"],
                "confirmed": "confirmed",
                "completed": "completed",
                "pending_approval": "pending",
                "rejected": "rejected"
            }
            if status in status_mapping_rev:
                mapped = status_mapping_rev[status]
                if isinstance(mapped, list):
                    filter_query["status"] = {"$in": mapped}
                else:
                    filter_query["status"] = mapped
            else:
                filter_query["status"] = status
        
        if vendor_type:
            filter_query["serviceProviderType"] = vendor_type
            
        if vendor_id:
            try:
                filter_query["serviceProviderId"] = ObjectId(vendor_id)
            except Exception:
                filter_query["serviceProviderId"] = vendor_id

        total_count = await db.bookings.count_documents(filter_query)
        cursor = db.bookings.find(filter_query).sort("createdAt", -1).skip(skip).limit(limit)
        
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
