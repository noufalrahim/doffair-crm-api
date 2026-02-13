
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
    collection = db["vendor_verticals"]
    
    print("🔄 Renaming fields in vendor_verticals collection...")
    
    # Rename service_type_id to vertical_id
    # Rename service_type_name to vertical_name (if it exists)
    result = await collection.update_many(
        {},
        {
            "$rename": {
                "service_type_id": "vertical_id",
                "service_type_name": "vertical_name"
            }
        }
    )
    
    print(f"✅ Successfully updated {result.modified_count} vendor_vertical documents.")
    print("🚀 Migration complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
