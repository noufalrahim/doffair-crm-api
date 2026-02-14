
import asyncio
import sys
from pathlib import Path
from bson import ObjectId

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

from vendor.models.care_professional import CareProfessional

async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    
    vertical_id = "69529fdb5a26a27c25c7c65a"
    vendor_id = "69905d49c857901ed124f37b"
    location_id = "699060e6c857901ed124f381"
    
    print(f"--- Debugging for Vertical: {vertical_id} ---")
    
    # 1. Check raw records in collection
    collection = db["care_professionals"]
    
    print(f"\n[Raw Search by vertical_id (as string)]")
    raw_results_str = await collection.find({"vertical_id": vertical_id}).to_list(None)
    print(f"Count: {len(raw_results_str)}")
    for r in raw_results_str:
        v_id = r.get('vendor_id')
        vert_id = r.get('vertical_id')
        print(f"ID: {r['_id']}, Name: {r.get('name')}")
        print(f"  Vendor: {v_id} (type: {type(v_id)})")
        print(f"  Vertical: {vert_id} (type: {type(vert_id)})")

    print("\n[Raw Search by vertical_id (as ObjectId)]")
    try:
        raw_results_oid = await collection.find({"vertical_id": ObjectId(vertical_id)}).to_list(None)
        print(f"Count: {len(raw_results_oid)}")
        for r in raw_results_oid:
            print(f"ID: {r['_id']}, Name: {r.get('name')}, Vendor: {r.get('vendor_id')}, Loc: {r.get('location_id')}")
    except:
        print("Invalid ObjectId format")

    print(f"\n[Raw Search for Location: {location_id}]")
    raw_location = await collection.find({"location_id": location_id}).to_list(None)
    print(f"Count: {len(raw_location)}")
    for r in raw_location:
        print(f"ID: {r['_id']}, Name: {r.get('name')}, Vendor: {r.get('vendor_id')}, Vertical: {r.get('vertical_id')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
