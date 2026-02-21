import asyncio
import os
from dotenv import load_dotenv
from core.database import get_engine
from admin.routers.vendors import get_all_vendor_bookings

async def main():
    load_dotenv()
    engine = get_engine()
    
    # Test walkin with pagination
    try:
        print("Testing walkin with skip=1, limit=5...")
        resp = await get_all_vendor_bookings(mode="walkin", skip=1, limit=5, engine=engine, _={"sub": "test_admin"})
        print("Walkin success:", list(resp.keys()))
        if resp.get("meta"):
            print("Walkin meta:", resp["meta"])
        if resp.get("data"):
            print(f"Returned {len(resp['data'])} walkin bookings")
    except Exception as e:
        print("Walkin error:", e)
        
    # Test online with pagination
    try:
        print("\nTesting online with skip=2, limit=3...")
        resp = await get_all_vendor_bookings(mode="online", skip=2, limit=3, engine=engine, _={"sub": "test_admin"})
        print("Online success:", list(resp.keys()))
        if resp.get("data"):
            print(f"Returned {len(resp['data'])} online bookings")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
