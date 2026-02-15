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
        
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]

    print(f"\n--- Collections in {db_name_secondary} (Secondary) ---")
    cols_s = await db_s.list_collection_names()
    for col in sorted(cols_s):
        print(f" - {col}")

if __name__ == "__main__":
    asyncio.run(debug())
