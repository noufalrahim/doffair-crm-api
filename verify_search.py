import asyncio
from core.database import get_secondary_engine
from vendor.routers.bookings import list_vendor_bookings

async def verify_search():
    vendor_id = "691c329574c5fa7b7c127cc9"
    token = {"vendor_id": vendor_id, "role": "vendor"}
    engine = get_secondary_engine()
    
    # 1. Search by User Email (Legacy/Modern)
    # Based on previous logs, user email was "amoghjoshi5868@gmail.com"
    search_term = "amogh" 
    print(f"--- Searching for '{search_term}' ---")
    try:
        response = await list_vendor_bookings(search=search_term, token=token, secondary_engine=engine)
        print(f"Found {len(response.data)} bookings.")
        for b in response.data:
            print(f" - {b.booking_id} | User: {b.user.name} | Email: {b.user.email}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Search by Pet Name (if known, otherwise try part of it)
    # Previous log didn't explicitly show pet name in summary but code extracts it.
    # Let's try searching "Unknown" if that's what returns, or maybe empty string just to see flow?
    # Better, let's just rely on the user search for verification primarily.
    
if __name__ == "__main__":
    asyncio.run(verify_search())
