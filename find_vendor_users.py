import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    print(f"--- Users with Vendor Role in {db_name} ---")
    cursor = db.users.find({"role": "vendor"}).limit(10)
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('firstName')} | Phone: {doc.get('phone')} | VendorID: {doc.get('vendor_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
