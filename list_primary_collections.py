import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    print(f"--- Collections in {db_name_primary} (Primary) ---")
    cols_p = await db_p.list_collection_names()
    for col in sorted(cols_p):
        print(f" - {col}")

if __name__ == "__main__":
    asyncio.run(debug())
