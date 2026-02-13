
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(".env")

MONGO_URL = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")

async def migrate():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    collections_to_rename = {
        "service_types": "verticals",
        "vendor_service_types": "vendor_verticals",
        "service_type_amenities": "vertical_amenities"
    }
    
    existing_collections = await db.list_collection_names()
    
    for old_name, new_name in collections_to_rename.items():
        if old_name in existing_collections:
            if new_name in existing_collections:
                print(f"⚠️  Warning: {new_name} already exists. Skipping rename for {old_name}")
            else:
                print(f"🔄 Renaming {old_name} to {new_name}...")
                await db[old_name].rename(new_name)
                print(f"✅ Successfully renamed {old_name} to {new_name}")
        else:
            print(f"ℹ️  Collection {old_name} not found, skipping.")

    print("🚀 Migration complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
