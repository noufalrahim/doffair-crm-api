import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    print(f"--- Bookings with vertical_name 'Vet' or 'veterinary' (Primary DB) ---")
    cursor = db_p["bookings"].find({
        "vertical_name": {"$regex": "vet", "$options": "i"}
    }).limit(20)
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Vertical: {doc.get('vertical_id')} | Name: {doc.get('vertical_name')} | Status: {doc.get('status')}")

if __name__ == "__main__":
    asyncio.run(debug())
