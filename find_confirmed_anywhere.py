import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def find_confirmed():
    from dotenv import load_dotenv
    load_dotenv()
    
    vendor_id = "69905d49c857901ed124f37b"
    
    # 1. Primary
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    print(f"--- Confirmed in Primary ({db_name}) for {vendor_id} ---")
    cursor = db.bookings.find({"vendor_id": vendor_id, "status": "confirmed"})
    async for d in cursor:
        print(f"PRIMARY | ID: {d['_id']} | Offline: {d.get('is_offline')} | Date: {d.get('booking_date')} | U: {d.get('user_name')}")

    # 2. Secondary
    uri2 = os.getenv("MONGODB_URI_SECONDARY")
    db_name2 = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client2 = AsyncIOMotorClient(uri2)
    db2 = client2[db_name2]
    
    from bson import ObjectId
    print(f"--- Confirmed in Secondary ({db_name2}) for {vendor_id} ---")
    query2 = {
        "$and": [
            {
                "$or": [
                    {"serviceProviderId": ObjectId(vendor_id)},
                    {"serviceProviderId": vendor_id},
                    {"vendor_id": vendor_id}
                ]
            },
            {"status": "confirmed"}
        ]
    }
    cursor2 = db2.bookings.find(query2)
    async for d2 in cursor2:
        print(f"SECONDARY | ID: {d2['_id']} | Start: {d2.get('startTime')} | SType: {d2.get('serviceProviderType')}")

if __name__ == "__main__":
    asyncio.run(find_confirmed())
