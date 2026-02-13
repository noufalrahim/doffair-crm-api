
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
    
    # Map of collection name to field renames
    migrations = {
        "vendor_services": {
            "service_type_id": "vertical_id",
            "service_type_name": "vertical_name"
        },
        "vendor_amenities": {
            "service_type_id": "vertical_id"
        },
        "holidays": {
            "service_type_id": "vertical_id"
        },
        "availability": {
            "service_type_id": "vertical_id"
        },
        "bookings": {
            "service_type_id": "vertical_id",
            "service_type_name": "vertical_name"
        },
        "leads": {
            "service_type_id": "vertical_id",
            "service_type_name": "vertical_name"
        }
    }
    
    for collection_name, field_map in migrations.items():
        print(f"🔄 Processing collection: {collection_name}...")
        
        # Build strict rename to avoid erroring if fields don't exist
        # But for $rename, we can just pass the map.
        result = await db[collection_name].update_many(
            {},
            {"$rename": field_map}
        )
        print(f"✅ Updated {result.modified_count} documents in {collection_name}")

    print("🚀 All field migrations complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
