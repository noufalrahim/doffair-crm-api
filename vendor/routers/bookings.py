from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine
from bson import ObjectId


from core.security import require_vendor
from utils.response import success_response
from user.models.booking import Booking
from user.models.payment import Payment
from user.models.payment import Payment
# from user.schemas.booking import BookingResponse


router = APIRouter(
    prefix="/vendor/bookings",
    tags=["Vendor Bookings"],
)


from vendor.schemas.booking import VendorBookingResponse, UserSummary, PetSummary, ServiceSummary, BookingStatusUpdate
from vendor.models.vendor_service import VendorService


async def map_booking_doc(booking_doc: dict, engine: AIOEngine) -> VendorBookingResponse:
    """Helper to map a raw booking document to VendorBookingResponse"""
    
    # helper variables
    _id_str = str(booking_doc["_id"])
    
    # Priority for ID:
    # 1. 'id' field (specific to bookings.id in secondary DB)
    # 2. 'booking_id' or 'bookingId'
    # 3. Fallback: raw _id string
    if booking_doc.get("is_offline"):
        booking_id = _id_str
    else:
        booking_id = booking_doc.get("id") or booking_doc.get("booking_id") or booking_doc.get("bookingId") or _id_str
    
    # --- Legacy Handling ---
    if "userId" in booking_doc and "user_id" not in booking_doc:
        # User
        user_name = "Unknown"
        user_phone = "Unknown"
        user_email = "Unknown"
        if booking_doc.get("userId"):
             user_id = booking_doc.get("userId")
             user_collection = engine.database.get_collection("users")
             user_doc = await user_collection.find_one({"_id": user_id})
             
             # Fetch UserInfo for Profile Image & Name
             user_info_collection = engine.database.get_collection("userInfo")
             # Try DBRef style query first as seen in inspection
             from bson import DBRef
             user_info = await user_info_collection.find_one({"userId": DBRef("users", user_id)})
             
             # Fallback if not found with DBRef, try direct ObjectId
             if not user_info:
                 user_info = await user_info_collection.find_one({"userId": user_id})

             if user_doc:
                 # Prefer name from UserInfo if available, else User doc
                 if user_info and user_info.get("name"):
                     user_name = user_info.get("name")
                 else:
                     user_name = user_doc.get("username", user_doc.get("firstName", "Unknown"))
                     
                 user_phone = user_doc.get("phoneNumber", user_doc.get("phone", "Unknown"))
                 user_email = user_doc.get("email", "Unknown")
                 
             user_image = None
             if user_info:
                 # Check common image field names
                 user_image = user_info.get("image") or user_info.get("profileImage") or user_info.get("avatar") or user_info.get("photo")

        # Pet
        pet_summary = None
        pet_id = booking_doc.get("petId")
        if pet_id:
             pet_collection = engine.database.get_collection("pets")
             pet_doc = await pet_collection.find_one({"_id": pet_id})
             if pet_doc:
                 weight_val = None
                 if isinstance(pet_doc.get("weight"), dict):
                      weight_val = float(pet_doc.get("weight", {}).get("value", 0))
                 elif isinstance(pet_doc.get("weight"), (int, float)):
                      weight_val = float(pet_doc.get("weight"))
                      
                 height_val = None
                 if isinstance(pet_doc.get("height"), dict):
                      height_val = float(pet_doc.get("height", {}).get("value", 0))
                 elif isinstance(pet_doc.get("height"), (int, float)):
                      height_val = float(pet_doc.get("height"))
                 
                 pet_summary = PetSummary(
                     name=pet_doc.get("petName"),
                     type=None,
                     breed=pet_doc.get("breed"),
                     age=pet_doc.get("age"),
                     weight=weight_val,
                     gender=pet_doc.get("gender"),
                     images=pet_doc.get("images", []),
                     
                     # Enriched Fields
                     about_me=pet_doc.get("aboutMe"),
                     height=height_val,
                     nature=pet_doc.get("petNature"),
                     energy_level=pet_doc.get("energyLevel"),
                     behavior=pet_doc.get("behaviour"), # UK spelling in DB
                     vaccinated=pet_doc.get("vaccinated"),
                     vaccination_validated=pet_doc.get("vaccinationValidated"),
                     vaccination_date=pet_doc.get("vaccinationDate"),
                 )

        # Service
        service_name = "Unknown Service"
        services_list = []
        raw_services = booking_doc.get("services", [])
        
        if raw_services and isinstance(raw_services, list):
            if len(raw_services) > 0:
                service_name = raw_services[0].get("name", "Unknown Service")
            
            for s in raw_services:
                s_id = s.get("serviceId")
                if isinstance(s_id, DBRef):
                    s_id = str(s_id.id)
                elif s_id:
                    s_id = str(s_id)
                    
                services_list.append(ServiceSummary(
                    id=s_id,
                    name=s.get("name", "Unknown"),
                    final_price=float(s.get("price", 0)),
                    discount=float(s.get("discount", 0)),
                    duration_minutes=int(s.get("duration", 0)),
                    status=s.get("status")
                ))

        # Status - No transformations
        status = booking_doc.get("status", "pending_payment")

        return VendorBookingResponse(
            id=booking_id,
            booking_date=booking_doc.get("startTime"),
            status=status if isinstance(status, str) else str(status),
            service_name=service_name,
            care_professional_id=(
                str(booking_doc.get("careProfessionalId"))
                if booking_doc.get("careProfessionalId") is not None
                else (
                    str(booking_doc.get("care_professional_id"))
                    if booking_doc.get("care_professional_id") is not None
                    else None
                )
            ),
            services=services_list,
            vertical_name=booking_doc.get("serviceType", "Unknown"),
            delivery_mode=booking_doc.get("delivery_mode", "In-Center"),
            final_amount=float(booking_doc.get("bookingAmount", 0)),
            vendor_notes=booking_doc.get("instructions"),
            created_at=booking_doc.get("createdAt"),
            user=UserSummary(name=user_name, phone=user_phone, email=user_email, image=user_image),
            pet=pet_summary
        )

    # --- Modern Handling ---
    booking = Booking.model_validate(booking_doc)
    
    # Map Modern Services (assuming same structure loosely or fields on booking?)
    # Booking model usually has detailed fields. Checking...
    # Booking model has `service_name`, but maybe not a list of services if it's single service booking?
    # Inspecting user/models/booking.py earlier showed: service_name, vertical_name.
    # It didn't explicitly show a `services` list field in the model definition I saw.
    # However, raw doc might have it if it's there.
    # Let's try to fetch `services` from raw doc even for modern if available, or just use single service details.
    
    modern_services_list = []
    raw_modern_services = booking_doc.get("services", [])
    if raw_modern_services and isinstance(raw_modern_services, list):
         for s in raw_modern_services:
                s_id = s.get("serviceId")
                if isinstance(s_id, DBRef):
                    s_id = str(s_id.id)
                elif s_id:
                    s_id = str(s_id)

                modern_services_list.append(ServiceSummary(
                    id=s_id,
                    name=s.get("name", "Unknown"),
                    final_price=float(s.get("price", 0)),
                    discount=float(s.get("discount", 0)),
                    duration_minutes=int(s.get("duration", 0)),
                    status=s.get("status")
                ))
    else:
        # Fallback if no list, create one from single service details
        # Status fallback for modern services list
        svc_status = booking_doc.get("status")
        if svc_status is None:
            svc_status = booking.status.value if hasattr(booking.status, 'value') else str(booking.status)

        modern_services_list.append(ServiceSummary(
            id=None, # Single service ID might be available on booking root?
            name=booking.service_name,
            final_price=booking.base_amount,
            discount=booking.discount_amount,
            duration_minutes=0, # Duration might not be on root
            status=svc_status if isinstance(svc_status, str) else str(svc_status)
        ))

    # Get payment details if exists (optional, keeping consistent with single view if needed, but list view is summary usually)
    # For performance, maybe skip payment query in list view? 
    # But VendorBookingResponse doesn't have payment status.
    
    # For Modern, we might also want to fetch UserInfo if not cached or if image needed
    # Modern booking has user_name, user_phone, user_email cached.
    # But image is likely NOT cached in Booking model.
    # So we should fetch UserInfo here too.
    user_image_modern = None
    if booking.user_id:
        try:
            # Need ObjectId
            u_id = ObjectId(booking.user_id)
            user_info_collection = engine.database.get_collection("userInfo")
            # Try DBRef
            from bson import DBRef
            user_info = await user_info_collection.find_one({"userId": DBRef("users", u_id)})
             
            if not user_info:
                 user_info = await user_info_collection.find_one({"userId": u_id})
                 
            if user_info:
                user_image_modern = user_info.get("image") or user_info.get("profileImage") or user_info.get("avatar") or user_info.get("photo")
        except Exception:
            pass # Ignore errors in optional fetch

    # Status handling for Modern
    raw_status = booking_doc.get("status")
    if raw_status is None:
        raw_status = booking.status.value if hasattr(booking.status, 'value') else str(booking.status)

    # Use prioritized/generated booking_id from the top of the function
    # Instead of str(booking.id), we use the booking_id we calculated
    
    return VendorBookingResponse(
            id=booking_id,
            booking_date=booking.booking_date,
            status=raw_status if isinstance(raw_status, str) else str(raw_status),
            service_name=booking.service_name,
            care_professional_id=booking.care_professional_id,
            services=modern_services_list,
            vertical_name=booking.vertical_name,
            delivery_mode=booking.delivery_mode,
            final_amount=booking.final_amount,
            vendor_notes=booking.vendor_notes,
            created_at=booking.created_at,
            user=UserSummary(
                name=booking.user_name,
                phone=booking.user_phone,
                email=booking.user_email,
                image=user_image_modern
            ),
            pet=PetSummary(
                name=booking.pet_name,
                type=booking.pet_type,
                breed=booking.pet_breed,
                age=booking.pet_age,
                weight=booking.pet_weight,
                gender=booking.pet_gender,
                height=booking.pet_height,
                vaccinated=booking.pet_vaccinated,
                about_me=booking.pet_about,
                medical_conditions=booking.pet_medical_conditions,
                special_notes=booking.pet_special_notes,
                images=booking.pet_images or []
            )
        )



from core.database import get_engine, get_secondary_engine
from admin.models.vertical import Vertical

@router.get("")
async def list_vendor_bookings(
    status: Optional[str] = None,
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    search: Optional[str] = None,
    vertical_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    primary_engine: AIOEngine = Depends(get_engine),
):
    """
    List all bookings for the authenticated vendor from the secondary database.
    Supports filters:
    - status: 'confirmed', 'pending', 'cancelled'
    - date range: start_date, end_date
    - search: booking_id (for now)
    - vertical_id: Filter by Vertical ID (Mandatory, returns empty if missing)
    - skip: Skip N results
    - limit: Limit results (default 50)
    """
    if not vertical_id:
        return success_response(data={"data": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    if not ObjectId.is_valid(vertical_id):
        return success_response(data={"data": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    vertical_doc = await primary_engine.database.get_collection("verticals").find_one(
        {"_id": ObjectId(vertical_id)}
    )
    if not vertical_doc:
        return success_response(data={"data": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    # Support both legacy "code" and requested "codes" key names
    raw_codes = vertical_doc.get("codes", vertical_doc.get("code", []))
    service_type_codes = [str(code).strip() for code in (raw_codes or []) if str(code).strip()]
    if not service_type_codes:
        return success_response(data={"data": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    vendor_id = str(token.get("vendor_id") or "")
    if not vendor_id:
        return success_response(data={"data": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    import re

    secondary_coll = secondary_engine.database.get_collection("bookings")
    provider_id_or = [{"serviceProviderId": vendor_id}, {"vendor_id": vendor_id}]
    if ObjectId.is_valid(vendor_id):
        provider_id_or.insert(0, {"serviceProviderId": ObjectId(vendor_id)})

    secondary_criteria = {
        "$and": [
            {"$or": provider_id_or},
            {"serviceProviderType": {"$in": service_type_codes}},
        ]
    }
    
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        # Search in users and pets if IDs are present, or search cached names if any
        # For legacy, we need to find userIds matching search
        user_coll = secondary_engine.database.get_collection("users")
        matching_users = await user_coll.find({
            "$or": [
                {"phoneNumber": search_regex},
                {"phone": search_regex},
                {"username": search_regex},
                {"firstName": search_regex},
                {"email": search_regex}
            ]
        }).to_list(length=200)
        
        search_user_ids = [u["_id"] for u in matching_users]
        
        pet_coll = secondary_engine.database.get_collection("pets")
        matching_pets = await pet_coll.find({
            "petName": search_regex
        }).to_list(length=200)
        
        search_pet_ids = [p["_id"] for p in matching_pets]
        
        search_or = [
            {"user_name": search_regex},
            {"user_phone": search_regex},
            {"user_email": search_regex},
            {"service_name": search_regex},
            {"pet_name": search_regex},
            {"instructions": search_regex},
            # Common field in some legacy docs
            {"name": search_regex},
            {"phone": search_regex}
        ]
        if search_user_ids:
            search_or.append({"userId": {"$in": search_user_ids}})
        if search_pet_ids:
            search_or.append({"petId": {"$in": search_pet_ids}})
            
        secondary_criteria["$and"].append({"$or": search_or})

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
            secondary_criteria["status"] = status
            
    if start_date or end_date:
        date_filter = {}
        if start_date: date_filter["$gte"] = start_date
        if end_date: date_filter["$lte"] = end_date
        secondary_criteria["startTime"] = date_filter

    legacy_cursor = secondary_coll.find(secondary_criteria).sort("createdAt", -1)
    online_bookings = []
    async for doc in legacy_cursor:
        try:
            mapped = await map_booking_doc(doc, secondary_engine)
            mapped.is_offline = False
            online_bookings.append(mapped)
        except Exception:
            continue

    total = len(online_bookings)
    paginated = online_bookings[skip : skip + limit]
    
    return success_response(data={
        "data": [b.model_dump() for b in paginated],
        "meta": {
            "total": total,
            "skip": skip,
            "limit": limit
        }
    })


@router.get("/combined")
async def list_combined_bookings(
    status: Optional[str] = None,
    start_date: Optional[datetime] = Query(None, alias="startDate"),
    end_date: Optional[datetime] = Query(None, alias="endDate"),
    search: Optional[str] = None,
    vertical_id: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    primary_engine: AIOEngine = Depends(get_engine),
):
    """
    List ALL bookings (Online + Offline) for the vendor.
    Merges results from both databases, sorts by date, and paginates.
    
    Simplified:
    - No search or status filtering.
    - Mandatory vertical_id.
    - If limit is None, returns ALL remaining records from skip.
    """
    if not vertical_id:
        return success_response(data={"bookings": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    vendor_id = token.get("vendor_id")
    
    # --- 1. Fetch Vertical Codes ---
    vertical_codes = []
    try:
         if ObjectId.is_valid(vertical_id):
             st = await primary_engine.find_one(Vertical, Vertical.id == ObjectId(vertical_id))
             if st:
                 vertical_codes = st.code
                 print(f"DEBUG: Resolved vertical_id {vertical_id} to codes {vertical_codes}")
             else:
                 print(f"DEBUG: Vertical {vertical_id} NOT FOUND in primary DB")
    except Exception as e:
         print(f"DEBUG: Error resolving vertical {vertical_id}: {e}")
         pass
    
    # If filter provided but no codes found, return empty matches immediately
    if not vertical_codes:
         print(f"DEBUG: Returning empty since no vertical_codes for {vertical_id}")
         return success_response(data={"bookings": [], "meta": {"total": 0, "skip": skip, "limit": limit}})

    # --- 2. Build Criteria for Online Bookings (Secondary DB) ---
    vendor_obj_id = None
    try:
        if ObjectId.is_valid(vendor_id):
            vendor_obj_id = ObjectId(vendor_id)
    except Exception:
        pass

    online_criteria = {
        "$and": [
            {
                "$or": [
                    {"serviceProviderId": vendor_obj_id} if vendor_obj_id else {"serviceProviderId": vendor_id}, 
                    {"serviceProviderId": vendor_id},           
                    {"vendor_id": vendor_id}                    
                ]
            },
            {"serviceProviderType": {"$in": vertical_codes}}
        ]
    }
    print(f"DEBUG: Online Criteria: {online_criteria}")
    
    # --- 3. Build Criteria for Primary DB Bookings (Online Modern + Offline) ---
    primary_criteria = {
        "vendor_id": vendor_id,
        "vertical_id": {"$in": [vertical_id, None]}
    }

    import re

    # --- Common Filters (Status) ---
    if status:
        st_lower = status.lower()
        if st_lower == "confirmed":
            online_criteria["status"] = "confirmed"
            primary_criteria["status"] = "confirmed"
        elif st_lower == "pending":
            online_criteria["status"] = {"$in": ["pending", "ongoing", "rescheduleRequest"]}
            primary_criteria["status"] = {"$in": ["pending", "ongoing", "pending_payment", "pending_approval"]}
        elif st_lower == "cancelled":
            online_criteria["status"] = {"$in": ["cancelled", "cancelByProvider", "rejected"]}
            primary_criteria["status"] = {"$in": ["cancelled", "rejected"]}
        elif st_lower == "completed":
            online_criteria["status"] = "completed"
            primary_criteria["status"] = "completed"
        else:
            online_criteria["status"] = status
            primary_criteria["status"] = status

    # --- Common Filters (Search) ---
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        
        # Online search (same as above)
        user_coll = secondary_engine.database.get_collection("users")
        matching_users = await user_coll.find({
            "$or": [
                {"phoneNumber": search_regex},
                {"phone": search_regex},
                {"username": search_regex},
                {"firstName": search_regex},
                {"email": search_regex}
            ]
        }).to_list(length=200)
        search_user_ids = [u["_id"] for u in matching_users]
        
        pet_coll = secondary_engine.database.get_collection("pets")
        matching_pets = await pet_coll.find({"petName": search_regex}).to_list(length=200)
        search_pet_ids = [p["_id"] for p in matching_pets]
        
        online_search_or = [
            {"user_name": search_regex},
            {"user_phone": search_regex},
            {"user_email": search_regex},
            {"service_name": search_regex},
            {"pet_name": search_regex},
            {"instructions": search_regex}
        ]
        if search_user_ids: online_search_or.append({"userId": {"$in": search_user_ids}})
        if search_pet_ids: online_search_or.append({"petId": {"$in": search_pet_ids}})
        online_criteria["$or"] = online_search_or

        # Primary DB search
        primary_criteria["$or"] = [
            {"user_name": search_regex},
            {"user_phone": search_regex},
            {"user_email": search_regex},
            {"service_name": search_regex},
            {"pet_name": search_regex},
            {"vendor_notes": search_regex}
        ]

    # --- Common Filters (Date) ---
    if start_date or end_date:
        date_filter = {}
        if start_date: date_filter["$gte"] = start_date
        if end_date: date_filter["$lte"] = end_date
        
        online_criteria["startTime"] = date_filter
        primary_criteria["booking_date"] = date_filter

    # --- 4. Execute Queries ---
    # Fetch Online
    online_coll = secondary_engine.database.get_collection("bookings")
    
    # Fetch ALL matching (Removed limit(200))
    online_cursor = online_coll.find(online_criteria).sort("createdAt", -1)
    
    online_docs = []
    found_count = 0
    async for doc in online_cursor:
         found_count += 1
         try:
             mapped = await map_booking_doc(doc, secondary_engine)
             mapped.is_offline = False
             online_docs.append(mapped)
         except Exception as e:
             print(f"DEBUG: Error mapping secondary doc {doc.get('_id')}: {e}")
             pass
    print(f"DEBUG: Found {found_count} secondary docs, successfully mapped {len(online_docs)}")

    # Fetch Primary DB results (Walk-ins)
    primary_walkin_coll = primary_engine.database.get_collection("walkin_bookings")
    primary_cursor = primary_walkin_coll.find(primary_criteria).sort("booking_date", -1)
    
    primary_docs = []
    primary_found_count = 0
    async for doc in primary_cursor:
        primary_found_count += 1
        try:
             # Ensure map_booking_doc knows it's offline if it doesn't have the field
             # But walkin_bookings usually have is_offline: True or we can set it
             if "is_offline" not in doc:
                 doc["is_offline"] = True
                 
             mapped = await map_booking_doc(doc, primary_engine)
             primary_docs.append(mapped)
        except Exception as e:
            print(f"DEBUG: Error mapping primary walkin {doc.get('_id')}: {e}")
            pass
    print(f"DEBUG: Found {primary_found_count} primary walkin docs, successfully mapped {len(primary_docs)}")

    # --- 5. Merge and Sort ---
    all_bookings = online_docs + primary_docs
    # Sort by created_at desc
    all_bookings.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    
    # --- 6. Paginate ---
    total = len(all_bookings)
    
    if limit is not None:
        paginated = all_bookings[skip : skip + limit]
    else:
        paginated = all_bookings[skip:]
    
    return success_response(
        data={
            "data": [b.model_dump() for b in paginated],
            "meta": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
    )


@router.get("/{booking_id}")
async def get_booking_details(
    booking_id: str,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    primary_engine: AIOEngine = Depends(get_engine),
):
    """
    Vendor views details of a specific booking by ID.
    Checks both:
    1) Primary DB: walkin_bookings (offline/walk-in)
    2) Secondary DB: bookings (online)
    """
    vendor_id = token.get("vendor_id")
    
    # Search by Multiple Possible ID fields
    search_query_list = [
        {"id": booking_id},
        {"booking_id": booking_id},
        {"bookingId": booking_id}
    ]
    
    if ObjectId.is_valid(booking_id):
        search_query_list.append({"_id": ObjectId(booking_id)})
    else:
        search_query_list.append({"_id": booking_id})

    search_query = {"$or": search_query_list}
    
    # 1. Check Primary walk-in bookings first
    collection_primary = primary_engine.database.get_collection("walkin_bookings")
    booking_doc = await collection_primary.find_one(search_query)
    current_engine = primary_engine
    
    if not booking_doc:
        # 2. Finally check secondary online bookings
        collection_secondary = secondary_engine.database.get_collection("bookings")
        booking_doc = await collection_secondary.find_one(search_query)
        current_engine = secondary_engine

    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify Vendor Ownership (Security)
    doc_vendor_id = booking_doc.get("vendor_id") or str(booking_doc.get("serviceProviderId") or "")
    if doc_vendor_id != vendor_id:
         raise HTTPException(status_code=403, detail="Access denied")

    # Use map_booking_doc for CONSISTENT mapping across all IDs
    try:
        res = await map_booking_doc(booking_doc, current_engine)
        return success_response(data=res)
    except Exception as e:
        print(f"Error mapping booking {booking_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error mapping booking data: {str(e)}")


@router.patch("/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status_update: BookingStatusUpdate,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
):
    """
    Update the status of a specific booking.
    Only allows updating status for online bookings in Secondary DB.
    """
    vendor_id = token.get("vendor_id")
    
    if not ObjectId.is_valid(booking_id):
        raise HTTPException(status_code=400, detail="Invalid booking ID")
        
    collection = secondary_engine.database.get_collection("bookings")
    booking_doc = await collection.find_one({"_id": ObjectId(booking_id)})
    
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify Ownership
    # Check if it's a legacy or modern doc to find serviceProviderId correctly
    is_owner = False
    if "userId" in booking_doc and "user_id" not in booking_doc:
        # Legacy
        if str(booking_doc.get("serviceProviderId")) == vendor_id:
            is_owner = True
    else:
        # Modern
        # Check against mapped model or raw fields
        # Note: mapped model might convert ID to string, so raw check is safer if mixed types
        # But let's use the field we know exists: likely 'serviceProviderId' or 'vendor_id'
        # Modern docs usually align with Booking model
        potential_vendor_ids = [
            booking_doc.get("serviceProviderId"),
            booking_doc.get("vendor_id")
        ]
        for vid in potential_vendor_ids:
            if str(vid) == vendor_id:
                is_owner = True
                break
    
    if not is_owner:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update Status
    # We update the raw document directly to ensure it works for both schemas if they share the 'status' field location
    # Both legacy and modern seem to have 'status' at root.
    
    new_status = status_update.status
    
    # Optional: Add validation for allowed status transitions if needed
    # For now, we trust the input as per request "if id and status is passed"
    
    await collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": new_status}}
    )
    
    return success_response(message="Booking status updated successfully")
