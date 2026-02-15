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
    
    vendor_id = "69905d49c857901ed124f37b"
    print(f"--- Checking Vendor {vendor_id} ---")
    doc = await db.vendors.find_one({"_id": vendor_id})
    if not doc:
        from bson import ObjectId
        doc = await db.vendors.find_one({"_id": ObjectId(vendor_id)})
    
    if doc:
        print(f"Vendor: {doc.get('name')} | VerticalID: {doc.get('vertical_id')} | VerticalIDs: {doc.get('vertical_ids')}")
    else:
        print("Vendor not found!")

if __name__ == "__main__":
    asyncio.run(debug())
