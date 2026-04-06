import asyncio
import os
import sys
from bson import ObjectId
from odmantic import AIOEngine

# Add project root to path
sys.path.append(os.getcwd())

from core.database import get_engine, get_secondary_engine
from vendor.services.invoice_service import handle_booking_completion_invoicing
from vendor.schemas.booking import BookingStatusUpdate

async def repair_booking_invoice(booking_id: str):
    primary_engine = get_engine()
    secondary_engine = get_secondary_engine()
    
    # 1. Fetch booking doc from either primary or secondary
    # We'll check secondary first since the errors found were [ONLINE]
    secondary_coll = secondary_engine.database.get_collection("bookings")
    booking_doc = await secondary_coll.find_one({"_id": ObjectId(booking_id)})
    
    if not booking_doc:
        primary_walkin_coll = primary_engine.database.get_collection("walkin_bookings")
        booking_doc = await primary_walkin_coll.find_one({"_id": ObjectId(booking_id)})
        
    if not booking_doc:
        print(f"❌ Booking {booking_id} not found in any database.")
        return

    # 2. Identify Vendor ID
    vendor_id = booking_doc.get("vendor_id") or str(booking_doc.get("serviceProviderId") or "")
    if not vendor_id:
        print(f"❌ Vendor ID not found for booking {booking_id}.")
        return

    print(f"Found booking {booking_id} for vendor {vendor_id}. Status: {booking_doc.get('status')}")
    
    if booking_doc.get('status') != 'completed':
        print(f"⚠️  Booking is not 'completed'. Current status: {booking_doc.get('status')}. Continuing anyway...")

    # 3. Trigger invoicing
    # handle_booking_completion_invoicing(engine, vendor_id, booking_doc, status_update, background_tasks)
    status_update = BookingStatusUpdate(status="completed")
    
    try:
        print(f"Triggering handle_booking_completion_invoicing for {booking_id}...")
        invoice = await handle_booking_completion_invoicing(
            primary_engine,
            str(vendor_id),
            booking_doc,
            status_update,
            None # background_tasks
        )
        
        if invoice:
            print(f"✅ Success! Generated Invoice: {invoice.invoice_number} (ID: {invoice.id})")
        else:
            print(f"❌ handle_booking_completion_invoicing returned None for {booking_id}.")
            
    except Exception as e:
        print(f"❌ Critical error during repair: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/repair_missing_invoices.py <booking_id>")
        sys.exit(1)
    
    target_id = sys.argv[1]
    asyncio.run(repair_booking_invoice(target_id))
