import asyncio
import os
from datetime import datetime
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from user.services.booking_service import get_vendor_bookings
from bson import ObjectId

async def mock_router():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    engine = AIOEngine(client=client, database=db_name)
    
    uri2 = os.getenv("MONGODB_URI_SECONDARY")
    db_name2 = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client2 = AsyncIOMotorClient(uri2)
    secondary_engine = AIOEngine(client=client2, database=db_name2)
    
    # User's Params
    vendor_id = "69905d49c857901ed124f37b"
    status = "confirmed"
    search = "geq"
    start_date = datetime.fromisoformat("2026-02-20T18:30:00.000+00:00").replace(tzinfo=None)
    end_date = datetime.fromisoformat("2026-02-26T18:30:00.000+00:00").replace(tzinfo=None)
    
    print(f"--- Mocking Router /bookings/vendor/my-bookings ---")
    
    # 1. Primary
    primary_status_filter = status.lower() if status else None
    primary_docs_tuples, _ = await get_vendor_bookings(
        engine, vendor_id, status_filter=primary_status_filter, 
        limit=10, skip=0, search=search, start_date=start_date, end_date=end_date
    )
    print(f"Primary Matches: {len(primary_docs_tuples)}")

    # 2. Secondary
    secondary_criteria = {
        "$and": [
            {
                "$or": [
                    {"serviceProviderId": ObjectId(vendor_id)},
                    {"serviceProviderId": vendor_id},
                    {"vendor_id": vendor_id}
                ]
            },
            {"status": "confirmed"}
        ]
    }
    # (Simplified secondary check for mock)
    secondary_count = await secondary_engine.database.get_collection("bookings").count_documents(secondary_criteria)
    print(f"Secondary Confirmed (All Time): {secondary_count}")

    # 3. Try WITHOUT "geq" search
    p2, _ = await get_vendor_bookings(
        engine, vendor_id, status_filter=primary_status_filter, 
        limit=10, skip=0, search=None, start_date=start_date, end_date=end_date
    )
    print(f"Primary Matches (without search): {len(p2)}")

    # 4. Try WITHOUT date filter (just confirmed + geq)
    p3, _ = await get_vendor_bookings(
        engine, vendor_id, status_filter=primary_status_filter, 
        limit=10, skip=0, search=search, start_date=None, end_date=None
    )
    print(f"Primary Matches (without date): {len(p3)}")

    # 5. Try WITHOUT search AND date (just confirmed for this vendor)
    p4, _ = await get_vendor_bookings(
        engine, vendor_id, status_filter=primary_status_filter, 
        limit=10, skip=0, search=None, start_date=None, end_date=None
    )
    print(f"Primary Matches (just confirmed): {len(p4)}")
    for b, p in p4:
        print(f"  FOUND: ID: {b['id']} | Date: {b.get('booking_date')} | U: {b.get('user_name')}")

if __name__ == "__main__":
    asyncio.run(mock_router())
