import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import re

async def global_search():
    from dotenv import load_dotenv
    load_dotenv()
    
    regex = re.compile("geq", re.I)
    
    for prefix in ["PRIMARY", "SECONDARY"]:
        uri = os.getenv(f"MONGODB_URI{'_SECONDARY' if prefix == 'SECONDARY' else ''}")
        db_name = os.getenv(f"MONGODB_DB_NAME{'_SECONDARY' if prefix == 'SECONDARY' else ''}")
        if not uri or not db_name: continue
        
        client = AsyncIOMotorClient(uri)
        db = client[db_name]
        print(f"\n--- Searching {prefix} DB: {db_name} ---")
        
        colls = await db.list_collection_names()
        for coll_name in colls:
            # We skip system collections
            if coll_name.startswith("system."): continue
            
            # Search in common fields
            try:
                # This is a bit brute force but let's try common string fields
                query = {"$or": [
                    {"name": regex},
                    {"user_name": regex},
                    {"username": regex},
                    {"email": regex},
                    {"phone": regex},
                    {"phoneNumber": regex},
                    {"service_name": regex},
                    {"notes": regex},
                    {"instructions": regex},
                    {"display_name": regex},
                    {"business_name": regex}
                ]}
                count = await db[coll_name].count_documents(query)
                if count > 0:
                    print(f"FOUND {count} matches in {coll_name}")
                    async for doc in db[coll_name].find(query).limit(5):
                        print(f"  Match in {coll_name}: {doc.get('_id')} | Title/Name: {doc.get('name') or doc.get('user_name') or doc.get('display_name')}")
            except Exception:
                continue

if __name__ == "__main__":
    asyncio.run(global_search())
