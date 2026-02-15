import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def search_secondary():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI_SECONDARY")
    db_name = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    vendor_id = "69905d49c857901ed124f37b"
    
    # 2026-02-20T18:30:00.000Z to 2026-02-26T18:30:00.000Z
    start = datetime.fromisoformat("2026-02-20T18:30:00+00:00").replace(tzinfo=None)
    end = datetime.fromisoformat("2026-02-26T18:30:00+00:00").replace(tzinfo=None)
    
    print(f"--- Bookings in ({db_name}) Range: {start} to {end} for {vendor_id} ---")
    query = {
        "$and": [
            {
                "$or": [
                    {"serviceProviderId": ObjectId(vendor_id)},
                    {"serviceProviderId": vendor_id},
                    {"vendor_id": vendor_id}
                ]
            },
            {"startTime": {"$gte": start, "$lte": end}},
            {"status": "confirmed"}
        ]
    }
    
    cursor = db.bookings.find(query)
    async for d in cursor:
        print(f"ID: {d['_id']} | Start: {d.get('startTime')} | S: {d.get('status')} | U: {d.get('user_name')}")

if __name__ == "__main__":
    asyncio.run(search_secondary())
