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
    
    print(f"--- Bookings with vertical_id ({db_name}) ---")
    doc = await db.bookings.find_one({"vertical_id": {"$ne": None}})
    if doc:
        print(f"ID: {doc['_id']} | VID: {doc.get('vertical_id')} | VID Type: {type(doc.get('vertical_id'))}")
    else:
        print("No bookings with vertical_id found in Primary DB!")

    uri_s = os.getenv("MONGODB_URI_SECONDARY")
    db_name_s = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_s)
    db_s = client_s[db_name_s]
    
    print(f"\n--- Bookings with vertical-like fields ({db_name_s}) ---")
    # In secondary it is serviceProviderType
    doc_s = await db_s.bookings.find_one({"serviceProviderType": {"$ne": None}})
    if doc_s:
        print(f"ID: {doc_s['_id']} | Type: {doc_s.get('serviceProviderType')} | Type Type: {type(doc_s.get('serviceProviderType'))}")

if __name__ == "__main__":
    asyncio.run(debug())
