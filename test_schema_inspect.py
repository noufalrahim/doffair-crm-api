import asyncio
import os
from dotenv import load_dotenv; load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    uri_sec = os.getenv("MONGODB_URI_SECONDARY")
    db_name_sec = os.getenv("MONGODB_DB_NAME_SECONDARY")
    uri_pri = os.getenv("MONGODB_URI")
    db_name_pri = os.getenv("MONGODB_DB_NAME")
    print(f"SEC DB: {db_name_sec}")
    print(f"PRI DB: {db_name_pri}")
    
    sec_client = AsyncIOMotorClient(uri_sec)
    db = sec_client[db_name_sec]

    # Get a sample booking
    booking = await db.bookings.find_one({})
    if not booking:
        print("No bookings found")
        return
    user_id = booking.get("userId")
    sp_id = booking.get("serviceProviderId")
    sp_type = booking.get("serviceProviderType", "")
    print(f"\nuserId={user_id}, serviceProviderId={sp_id}, serviceProviderType={sp_type}")

    from bson import ObjectId
    try:
        uid = ObjectId(user_id)
    except:
        uid = user_id

    user = await db.users.find_one({"_id": uid})
    print("\n--- User (from users collection) ---")
    if user:
        print(list(user.keys()))
        print("email:", user.get("email"), "| phone:", user.get("phone") or user.get("mobileNumber"))
    else:
        print("User not found with _id:", uid)

    # Try userInfo collection
    user_info = await db.userInfo.find_one({"userId": str(uid)})
    if not user_info:
        user_info = await db.userInfo.find_one({"userId": uid})
    print("\n--- UserInfo collection ---")
    if user_info:
        print(list(user_info.keys()))
        print("name:", user_info.get("name") or user_info.get("firstName") or user_info.get("fullName"))
    else:
        print("userInfo not found for userId:", uid)

    # groomerInfoNew sample
    groomer = await db.groomerInfoNew.find_one({})
    print("\n--- GroomerInfoNew sample keys ---")
    if groomer:
        print(list(groomer.keys()))
        print("name:", groomer.get("name") or groomer.get("fullName") or groomer.get("businessName"))
    else:
        print("No groomerInfoNew documents found")

    # vetInfo sample
    vet = await db.vetInfo.find_one({})
    print("\n--- VetInfo sample keys ---")
    if vet:
        print(list(vet.keys()))
        print("name:", vet.get("name") or vet.get("fullName") or vet.get("businessName"))
    else:
        print("No vetInfo documents found")

if __name__ == "__main__":
    asyncio.run(main())
