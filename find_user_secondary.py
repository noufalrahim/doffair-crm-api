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
    
    print(f"--- Users in {db_name} (Secondary) ---")
    cursor = db.users.find({
        "$or": [
            {"firstName": {"$regex": "noufal", "$options": "i"}},
            {"username": {"$regex": "noufal", "$options": "i"}},
            {"role": "vendor"}
        ]
    }).limit(10)
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('firstName')} | Phone: {doc.get('phone')} | Role: {doc.get('role')} | Vendor: {doc.get('vendorId')}")

if __name__ == "__main__":
    asyncio.run(debug())
