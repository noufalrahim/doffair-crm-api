from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

from core.database import get_engine, get_secondary_engine
from core.security import require_vendor
from utils.response import success_response
from user.models.booking import Booking
from vendor.schemas.customer import CustomerPetDiscoveryResponse
from vendor.schemas.booking import PetSummary

router = APIRouter(
    prefix="/vendor/customers",
    tags=["Vendor - Customers Discovery"]
)

@router.get("", response_model=dict)
async def get_vendor_customers(
    phone: Optional[str] = None,
    name: Optional[str] = None,
    search: Optional[str] = None,
    token: dict = Depends(require_vendor()),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    primary_engine: AIOEngine = Depends(get_engine),
):
    """
    Get all unique customers and their pet information for the authenticated vendor.
    Aggregates data from both online (secondary DB) and offline (primary DB) bookings.
    
    Query params:
        phone: Filter by exact phone number
        name: Filter by name (case-insensitive substring match)
        search: Search across both phone and name fields (case-insensitive substring)
    """
    vendor_id = token.get("vendor_id")
    
    customers_dict = {} # Key: (phone, email)
    
    import re
    
    # --- 1. Fetch Online Bookings (Secondary DB) ---
    online_coll = secondary_engine.get_collection(Booking)
    online_criteria = {
        "$and": [
            {
                "$or": [
                    {"serviceProviderId": ObjectId(vendor_id)}, 
                    {"serviceProviderId": vendor_id},           
                    {"vendor_id": vendor_id}                    
                ]
            }
        ]
    }
    
    if phone:
        online_criteria["$and"].append({
            "$or": [
                {"user_phone": phone},
                {"phone": phone},
                {"userId": {"$in": []}} # Placeholder for phone lookup if needed
            ]
        })
        # If filtering by phone, we should also find the userIds matching this phone
        user_coll = secondary_engine.database.get_collection("users")
        matching_users = await user_coll.find({
            "$or": [{"phoneNumber": phone}, {"phone": phone}]
        }).to_list(length=100)
        
        if matching_users:
            u_ids = [u["_id"] for u in matching_users]
            online_criteria["$and"][-1]["$or"].append({"userId": {"$in": u_ids}})
    
    if name:
        name_regex = {"$regex": re.escape(name), "$options": "i"}
        online_criteria["$and"].append({
            "$or": [
                {"user_name": name_regex},
                {"name": name_regex},
            ]
        })
    
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        search_user_ids = []
        # Also search users collection for matching phone/name
        user_coll = secondary_engine.database.get_collection("users")
        matching_users = await user_coll.find({
            "$or": [
                {"phoneNumber": search_regex},
                {"phone": search_regex},
                {"username": search_regex},
                {"firstName": search_regex},
            ]
        }).to_list(length=200)
        if matching_users:
            search_user_ids = [u["_id"] for u in matching_users]
        
        search_or = [
            {"user_phone": search_regex},
            {"phone": search_regex},
            {"user_name": search_regex},
            {"name": search_regex},
        ]
        if search_user_ids:
            search_or.append({"userId": {"$in": search_user_ids}})
        online_criteria["$and"].append({"$or": search_or})
    
    online_cursor = online_coll.find(online_criteria)
    
    # --- 2. Fetch Offline Bookings (Primary DB) ---
    offline_coll = primary_engine.get_collection(Booking)
    offline_criteria = {
        "vendor_id": vendor_id,
        "is_offline": True
    }
    if phone:
        offline_criteria["user_phone"] = phone
    if name:
        offline_criteria["user_name"] = {"$regex": re.escape(name), "$options": "i"}
    if search:
        search_regex_val = {"$regex": re.escape(search), "$options": "i"}
        offline_criteria["$or"] = [
            {"user_phone": search_regex_val},
            {"user_name": search_regex_val},
        ]
    offline_cursor = offline_coll.find(offline_criteria)

    # Merge and Sort Bookings to find most recent pet per customer
    all_booking_docs = []
    
    async for doc in online_cursor:
        doc["_sort_date"] = doc.get("createdAt") or datetime.min
        doc["_source"] = "online"
        all_booking_docs.append(doc)
        
    async for doc in offline_cursor:
        doc["_sort_date"] = doc.get("booking_date") or doc.get("created_at") or datetime.min
        doc["_source"] = "offline"
        all_booking_docs.append(doc)
        
    # Sort DESC by date
    all_booking_docs.sort(key=lambda x: x["_sort_date"], reverse=True)
    
    for doc in all_booking_docs:
        try:
            if doc["_source"] == "online":
                # --- Field Discovery ---
                phone = doc.get("user_phone", doc.get("phone"))
                email = doc.get("user_email", doc.get("email"))
                name = doc.get("user_name", doc.get("name"))
                
                # --- Legacy User Handling ---
                if not phone or (name == "Unknown" or not name):
                    user_id = doc.get("userId")
                    if user_id:
                        user_coll = secondary_engine.database.get_collection("users")
                        user_doc = await user_coll.find_one({"_id": user_id})
                        if user_doc:
                            if not phone:
                                phone = user_doc.get("phoneNumber", user_doc.get("phone"))
                            if not email:
                                email = user_doc.get("email")
                            if not name or name == "Unknown":
                                name = user_doc.get("username", user_doc.get("firstName", "Unknown"))
                                user_info_coll = secondary_engine.database.get_collection("userInfo")
                                from bson import DBRef
                                user_info = await user_info_coll.find_one({"userId": DBRef("users", user_id)})
                                if not user_info:
                                    user_info = await user_info_coll.find_one({"userId": user_id})
                                if user_info and user_info.get("name"):
                                    name = user_info.get("name")

                if not phone: continue

                key = (phone, email)
                if key in customers_dict: continue # Already have most recent

                # --- Pet Handling ---
                pet_name = doc.get("pet_name")
                pet_summary = None
                
                if pet_name:
                    pet_summary = PetSummary(
                        name=pet_name,
                        type=doc.get("pet_type"),
                        breed=doc.get("pet_breed"),
                        age=doc.get("pet_age"),
                        weight=doc.get("pet_weight"),
                        gender=doc.get("pet_gender"),
                        images=doc.get("pet_images", [])
                    )
                else:
                    pet_id = doc.get("petId")
                    if pet_id:
                        pet_coll = secondary_engine.database.get_collection("pets")
                        pet_doc = await pet_coll.find_one({"_id": pet_id})
                        if pet_doc:
                            pet_name = pet_doc.get("petName")
                            weight_val = None
                            if isinstance(pet_doc.get("weight"), dict):
                                weight_val = float(pet_doc.get("weight", {}).get("value", 0))
                            elif isinstance(pet_doc.get("weight"), (int, float)):
                                weight_val = float(pet_doc.get("weight"))

                            pet_summary = PetSummary(
                                name=pet_name,
                                type=None,
                                breed=pet_doc.get("breed"),
                                age=pet_doc.get("age"),
                                gender=pet_doc.get("gender"),
                                weight=weight_val,
                                images=pet_doc.get("images", [])
                            )

                # Resolve user_id for this customer
                user_id_str = None
                raw_user_id = doc.get("userId") or doc.get("user_id")
                if raw_user_id:
                    user_id_str = str(raw_user_id)
                # Also try looking up by phone to get the canonical user ID
                if not user_id_str and phone:
                    user_coll2 = secondary_engine.database.get_collection("users")
                    u = await user_coll2.find_one({"$or": [{"phoneNumber": phone}, {"phone": phone}]})
                    if u:
                        user_id_str = str(u["_id"])

                customers_dict[key] = CustomerPetDiscoveryResponse(
                    id=user_id_str,
                    name=name or "Unknown",
                    email=email,
                    phone=phone,
                    pet=pet_summary
                )

            else: # Offline
                phone = doc.get("user_phone")
                name = doc.get("user_name", "Unknown")
                email = doc.get("user_email")
                
                if not phone: continue
                
                key = (phone, email)
                if key in customers_dict: continue # Already have most recent

                pet_name = doc.get("pet_name")
                pet_summary = None
                if pet_name:
                    pet_summary = PetSummary(
                        name=pet_name,
                        type=doc.get("pet_type"),
                        breed=doc.get("pet_breed"),
                        age=doc.get("pet_age"),
                        weight=doc.get("pet_weight"),
                        gender=doc.get("pet_gender"),
                        images=doc.get("pet_images", [])
                    )
                    
                # For offline bookings, look up user by phone to get their ID
                offline_user_id_str = None
                if phone:
                    user_coll3 = secondary_engine.database.get_collection("users")
                    ou = await user_coll3.find_one({"$or": [{"phoneNumber": phone}, {"phone": phone}]})
                    if ou:
                        offline_user_id_str = str(ou["_id"])
                    
                customers_dict[key] = CustomerPetDiscoveryResponse(
                    id=offline_user_id_str,
                    name=name,
                    email=email,
                    phone=phone,
                    pet=pet_summary
                )
        except Exception as e:
            print(f"Error processing booking {doc.get('_id')}: {e}")
            continue


    return success_response(data=[c.model_dump() for c in customers_dict.values()]).model_dump()
