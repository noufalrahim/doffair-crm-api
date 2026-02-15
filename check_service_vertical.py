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
    print(f"--- Checking Services for Vendor {vendor_id} ---")
    cursor = db.vendor_services.find({"vendor_id": vendor_id})
    async for doc in cursor:
        print(f"Service: {doc.get('name')} | VerticalID: {doc.get('vertical_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
