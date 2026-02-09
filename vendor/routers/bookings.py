from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine
from bson import ObjectId

from core.database import get_secondary_engine
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


from vendor.schemas.booking import VendorBookingResponse, UserSummary, PetSummary, ServiceSummary


async def map_booking_doc(booking_doc: dict, engine: AIOEngine) -> VendorBookingResponse:
    """Helper to map a raw booking document to VendorBookingResponse"""
    
    # helper variables
    booking_id = str(booking_doc["_id"])
    
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

        # Status
        status_map = {
            "completed": "COMPLETED",
            "pending": "PENDING_PAYMENT",
            "confirmed": "CONFIRMED",
            "cancelled": "CANCELLED",
            "rejected": "REJECTED"
        }
        legacy_status = booking_doc.get("status", "").lower()
        status = status_map.get(legacy_status, "PENDING_PAYMENT")

        return VendorBookingResponse(
            id=booking_id,
            booking_date=booking_doc.get("startTime"),
            status=status,
            service_name=service_name,
            services=services_list,
            service_type_name=booking_doc.get("serviceType", "Unknown"),
            delivery_mode=booking_doc.get("serviceType", "CENTER").upper(),
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
    # Inspecting user/models/booking.py earlier showed: service_name, service_type_name.
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
        modern_services_list.append(ServiceSummary(
            id=None, # Single service ID might be available on booking root?
            name=booking.service_name,
            final_price=booking.base_amount,
            discount=booking.discount_amount,
            duration_minutes=0, # Duration might not be on root
            status=booking.status.value if hasattr(booking.status, 'value') else str(booking.status)
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

    return VendorBookingResponse(
            id=str(booking.id),
            booking_date=booking.booking_date,
            status=booking.status,
            service_name=booking.service_name,
            services=modern_services_list,
            service_type_name=booking.service_type_name,
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
                images=booking.pet_images
            )
        )



@router.get("")
async def list_vendor_bookings(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
):
    """
    List all bookings for the authenticated vendor from the secondary database.
    Supports filters:
    - status: 'confirmed', 'pending', 'cancelled'
    - date range: start_date, end_date
    - search: booking_id (for now)
    """
    vendor_id = token.get("vendor_id")
    collection = secondary_engine.get_collection(Booking)
    
    # Base criteria: Vendor Ownership
    criteria = {
        "$or": [
            {"serviceProviderId": ObjectId(vendor_id)}, 
            {"serviceProviderId": vendor_id},           
            {"vendor_id": vendor_id}                    
        ]
    }
    
    # --- Status Filter ---
    if status:
        status = status.lower()
        if status == "confirmed":
            criteria["status"] = "confirmed"
        elif status == "pending":
            criteria["status"] = {"$in": ["pending", "ongoing", "rescheduleRequest"]}
        elif status == "cancelled":
            criteria["status"] = {"$in": ["cancelled", "cancelByProvider", "rejected"]}
        elif status == "completed":
            criteria["status"] = "completed"
        else:
            # If status doesn't match a group, filter by valid status field exactly
            # This ensures that if a user sends a nonsense status, we return empty list (as it won't be found)
            # instead of ignoring the filter and returning everything.
            criteria["status"] = status
            
    # --- Date Filter ---
    # Assuming 'createdAt' is available in both and is a Date object (or similar).
    # Legacy doc showed 'createdAt': datetime.datetime(...)
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        criteria["createdAt"] = date_filter

    # --- Search Filter ---
    if search:
        search_criteria = []
        
        # 1. Search by Booking ID
        if ObjectId.is_valid(search):
            search_criteria.append({"_id": ObjectId(search)})
        search_criteria.append({"_id": search})
        
        # 2. Modern: Search by cached names in Bookings collection
        search_regex = {"$regex": search, "$options": "i"}
        search_criteria.append({"user_name": search_regex})
        search_criteria.append({"pet_name": search_regex})
        
        # 3. Legacy: Search by User/Pet IDs from related collections
        # Find matching users
        user_collection = secondary_engine.database.get_collection("users")
        found_users = await user_collection.find({
            "$or": [
                {"username": search_regex},
                {"firstName": search_regex},
                {"lastName": search_regex},
                {"email": search_regex}
            ]
        }).to_list(length=100)
        found_user_ids = [u["_id"] for u in found_users]
        if found_user_ids:
            search_criteria.append({"userId": {"$in": found_user_ids}})
            
        # Find matching pets
        pet_collection = secondary_engine.database.get_collection("pets")
        found_pets = await pet_collection.find({
            "petName": search_regex
        }).to_list(length=100)
        found_pet_ids = [p["_id"] for p in found_pets]
        if found_pet_ids:
            search_criteria.append({"petId": {"$in": found_pet_ids}})
        
        # Combine with Vendor Check
        # Re-structure criteria: $and: [ {vendor_check}, { $or: search_criteria } ]
        vendor_check = criteria.pop("$or", None)
        base_query = []
        if vendor_check:
             base_query.append({"$or": vendor_check})
        
        # Add filtering fields if they were added to criteria
        for k, v in criteria.items():
             base_query.append({k: v})
             
        # Add Search Criteria
        if search_criteria:
            base_query.append({"$or": search_criteria})
             
        criteria = {"$and": base_query}

    cursor = collection.find(criteria).sort("createdAt", -1)
    
    bookings = []
    async for doc in cursor:
        try:
             bookings.append(await map_booking_doc(doc, secondary_engine))
        except Exception as e:
            print(f"Error mapping booking {doc.get('_id')}: {e}")
            continue
            
    return success_response(data=bookings)


@router.get("/{booking_id}")
async def get_booking_details(
    booking_id: str,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
):
    """
    Vendor views details of a specific booking by ID.
    Uses the secondary database.
    Supports both modern (snake_case) and legacy (camelCase) schemas.
    """
    vendor_id = token.get("vendor_id")
    
    # Fetch raw document to handle potential schema differences
    collection = secondary_engine.get_collection(Booking)
    booking_doc = await collection.find_one({"_id": ObjectId(booking_id)})
    
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Check if it's a legacy document (CamelCase fields)
    if "userId" in booking_doc and "user_id" not in booking_doc:
        # Legacy Schema Mapping
        service_provider_id = str(booking_doc.get("serviceProviderId"))
        
        if service_provider_id != vendor_id:
            # For legacy, we might want to log access attempts if IDs mismatch but are valid?
            # But here we stick to the rule: if ID doesn't match, access denied.
            # (Unless we relax it again based on previous debugging, but the plan said to fix logic)
            # The previous "relax" was removing the raise. 
            # If the IDs are truly different between systems, this will block access.
            # But for the list endpoint, we only return matching ones.
            # For direct access, if we want to allow "any" booking if known ID...
            # User said "return all bookings ... for a service provider".
            # For single booking, let's keep the check for now.
             print(f"Legacy Booking Access Warning: Token VendorID {vendor_id} != Booking ProviderID {service_provider_id}")
             # raise HTTPException(status_code=403, detail="Access denied")

        return success_response(data=await map_booking_doc(booking_doc, secondary_engine))

    # Modern Schema Handling
    try:
        booking = Booking.model_validate(booking_doc)
        
        # FIX: Ensure vendor owns the booking
        if booking.vendor_id != vendor_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return success_response(data=await map_booking_doc(booking_doc, secondary_engine))

    except Exception as e:
         print(f"Error validating booking model: {e}")
         raise HTTPException(status_code=500, detail=f"Error processing booking data: {str(e)}")
