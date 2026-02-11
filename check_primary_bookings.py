
import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv(".env")

# Mongo config
MONGO_URL = os.getenv("MONGODB_URI") 
DB_NAME = os.getenv("MONGODB_DB_NAME")

async def check_primary():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db["bookings"]
    
    vendor_id = "69881a54d1bbd0a7b3f6d2bf"
    
    print(f"--- Checking Primary DB Bookings for Vendor {vendor_id} ---")
    count = await collection.count_documents({"vendor_id": vendor_id})
    print(f"Total bookings: {count}")
    
    if count > 0:
        docs = await collection.find({"vendor_id": vendor_id}).limit(2).to_list(length=2)
        import json
        from datetime import datetime
        class JSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, ObjectId): return str(obj)
                if isinstance(obj, datetime): return obj.isoformat()
                return super().default(obj)
        print(json.dumps(docs, indent=2, cls=JSONEncoder))

if __name__ == "__main__":
    asyncio.run(check_primary())
