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
    
    doc_id = "6991507bb67d2e018f6cfe07"
    print(f"--- Checking Booking {doc_id} ---")
    doc = await db.bookings.find_one({"_id": doc_id})
    if not doc:
        doc = await db.bookings.find_one({"_id": ObjectId(doc_id)})
        
    if doc:
        for key in ["vertical_id", "vendor_id", "booking_date", "status"]:
            val = doc.get(key)
            print(f"{key}: {val} | Type: {type(val)}")
    else:
        print("Booking not found!")

if __name__ == "__main__":
    from bson import ObjectId
    asyncio.run(debug())
