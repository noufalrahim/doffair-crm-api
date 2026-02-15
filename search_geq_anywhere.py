import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import re

async def search_geq():
    from dotenv import load_dotenv
    load_dotenv()
    
    # 1. Primary
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    regex = re.compile("geq", re.I)
    print(f"--- Searching for 'geq' in Primary ({db_name}) ---")
    query = {
        "$or": [
            {"user_name": regex},
            {"user_phone": regex},
            {"user_email": regex},
            {"service_name": regex},
            {"pet_name": regex},
            {"vendor_notes": regex}
        ]
    }
    cursor = db.bookings.find(query)
    async for d in cursor:
        print(f"PRIMARY | ID: {d['_id']} | Date: {d.get('booking_date')} | SName: {d.get('service_name')} | UName: {d.get('user_name')}")

    # 2. Secondary
    uri2 = os.getenv("MONGODB_URI_SECONDARY")
    db_name2 = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client2 = AsyncIOMotorClient(uri2)
    db2 = client2[db_name2]
    
    print(f"--- Searching for 'geq' in Secondary ({db_name2}) ---")
    # Secondary has different fields
    query2 = {
        "$or": [
            {"user_name": regex},
            {"name": regex},
            {"service_name": regex},
            {"instructions": regex}
        ]
    }
    cursor2 = db2.bookings.find(query2)
    async for d in cursor2:
        print(f"SECONDARY | ID: {d['_id']} | Start: {d.get('startTime')} | SName: {d.get('service_name')} | Status: {d.get('status')}")

if __name__ == "__main__":
    asyncio.run(search_geq())
