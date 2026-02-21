import asyncio
import os
from dotenv import load_dotenv; load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def main():
    uri_sec = os.getenv("MONGODB_URI_SECONDARY")
    db_name_sec = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri_sec)
    db = client[db_name_sec]
    
    uri_pri = os.getenv("MONGODB_URI")
    db_name_pri = os.getenv("MONGODB_DB_NAME")
    pri_client = AsyncIOMotorClient(uri_pri)
    pri_db = pri_client[db_name_pri]

    booking = await db.bookings.find_one({})
    if not booking:
        print("No bookings found")
        return
        
    bid = str(booking["_id"])
    uid = booking.get("userId")
    vid = booking.get("serviceProviderId")
    sp_type = booking.get("serviceProviderType")
    
    print(f"--- TRACE BOOKING {bid} ---")
    print(f"userId: {uid} | serviceProviderId: {vid} | sp_type: {sp_type}")
    
    # User Resolution Trace
    print("\n[USER TRACE]")
    try:
        u_oid = ObjectId(uid) if isinstance(uid, str) and len(uid) == 24 else uid
        u_doc = await db.users.find_one({"_id": u_oid})
        print(f" - users coll lookup: {'FOUND' if u_doc else 'NOT FOUND'}")
        if u_doc:
            print(f"   email: {u_doc.get('email')}, phoneNumber: {u_doc.get('phoneNumber')}")
        
        ui_doc = await db.userInfo.find_one({"userId": str(u_oid)}) or await db.userInfo.find_one({"userId": u_oid})
        print(f" - userInfo coll lookup: {'FOUND' if ui_doc else 'NOT FOUND'}")
        if ui_doc:
            print(f"   name field: {ui_doc.get('name') or ui_doc.get('firstName') or ui_doc.get('fullName')}")
    except Exception as e:
        print(f" - User Trace Error: {e}")

    # Vendor Resolution Trace
    print("\n[VENDOR TRACE]")
    try:
        v_oid = ObjectId(vid) if isinstance(vid, str) and len(vid) == 24 else vid
        found_v = None
        if sp_type == "groomer":
            found_v = await db.groomerInfoNew.find_one({"_id": v_oid})
            print(f" - groomerInfoNew lookup: {'FOUND' if found_v else 'NOT FOUND'}")
        elif sp_type == "vet":
            found_v = await db.vetInfo.find_one({"_id": v_oid})
            print(f" - vetInfo lookup: {'FOUND' if found_v else 'NOT FOUND'}")
            if not found_v:
                found_v = await db.groomerInfoNew.find_one({"_id": v_oid})
                print(f" - groomerInfoNew fallback lookup: {'FOUND' if found_v else 'NOT FOUND'}")
            if not found_v:
                found_v = await pri_db.vendors.find_one({"_id": v_oid})
                print(f" - primary vendors fallback lookup: {'FOUND' if found_v else 'NOT FOUND'}")
        
        if found_v:
            name = found_v.get("name") or found_v.get("businessName") or found_v.get("fullName") or found_v.get("business_name")
            print(f" - Decided name: {name}")
    except Exception as e:
        print(f" - Vendor Trace Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
