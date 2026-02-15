import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI_SECONDARY")
    db_name = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    print(f"--- Completed 'vet' Bookings in {db_name} ---")
    # Using regex for case insensitivity on both status and type
    cursor = db.bookings.find({
        "status": {"$regex": "completed", "$options": "i"},
        "serviceProviderType": {"$regex": "vet", "$options": "i"}
    }).limit(10)
    
    async for d in cursor:
        print(f"ID: {d['_id']} | Start: {d.get('startTime')} | S: {d.get('status')} | V: {d.get('serviceProviderId')} | Type: {d.get('serviceProviderType')}")

if __name__ == "__main__":
    asyncio.run(debug())
