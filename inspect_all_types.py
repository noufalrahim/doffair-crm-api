
import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

MONGO_URL_SECONDARY = os.getenv("MONGODB_URI_SECONDARY")
DB_NAME_SECONDARY = os.getenv("MONGODB_DB_NAME_SECONDARY")

async def inspect():
    client = AsyncIOMotorClient(MONGO_URL_SECONDARY)
    db = client[DB_NAME_SECONDARY]
    collection = db["bookings"]
    
    vendor_id = "69881a54d1bbd0a7b3f6d2bf"
    
    print(f"--- All Bookings for Vendor {vendor_id} in Secondary DB ---")
    docs = await collection.find({
        "$or": [
            {"serviceProviderId": vendor_id},
            {"serviceProviderId": ObjectId(vendor_id)},
            {"vendor_id": vendor_id}
        ]
    }).to_list(length=100)
    
    types_found = {}
    for doc in docs:
        sp_type = doc.get("serviceProviderType")
        st_name = doc.get("service_type_name")
        st_legacy = doc.get("serviceType")
        
        key = f"SPT:{sp_type} | STN:{st_name} | ST:{st_legacy}"
        types_found[key] = types_found.get(key, 0) + 1
        
    for k, v in types_found.items():
        print(f"{k}: {v} docs")

if __name__ == "__main__":
    asyncio.run(inspect())
