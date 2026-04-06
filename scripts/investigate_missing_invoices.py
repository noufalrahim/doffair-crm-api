import asyncio
import os
import sys
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to path
# CWD should be doffair-python-vendor/
sys.path.append(os.getcwd())

from core.database import get_engine, get_secondary_engine
from vendor.models.invoice import Invoice
from vendor.models.transaction import Transaction

async def investigate_missing_invoices():
    primary_engine = get_engine()
    secondary_engine = get_secondary_engine()
    
    # Check both DBs for completed bookings in the last 24h
    since = datetime.utcnow() - timedelta(hours=24)
    print(f"--- Scanning for completed bookings since {since} ---")
    
    # 1. Secondary DB (Online Bookings)
    secondary_coll = secondary_engine.database.get_collection("bookings")
    online_completed = await secondary_coll.find({
        "status": "completed",
        "updatedAt": {"$gte": since}
    }).to_list(length=100)
    
    # 2. Primary DB (Walk-in Bookings)
    primary_walkin_coll = primary_engine.database.get_collection("walkin_bookings")
    offline_completed = await primary_walkin_coll.find({
        "status": "completed",
        "updatedAt": {"$gte": since}
    }).to_list(length=100)
    
    all_completed = []
    for doc in online_completed:
        all_completed.append({'id': str(doc.get("_id")), 'type': 'ONLINE', 'doc': doc})
    for doc in offline_completed:
        all_completed.append({'id': str(doc.get("_id")), 'type': 'OFFLINE', 'doc': doc})
        
    print(f"Found {len(all_completed)} total completed bookings in the scan window.")
    
    missing_invoices = 0
    missing_transactions = 0
    
    for item in all_completed:
        booking_id = item['id']
        invoice = await primary_engine.find_one(Invoice, Invoice.booking_id == booking_id)
        
        if not invoice:
            print(f"❌ MISSING INVOICE: [{item['type']}] Booking {booking_id} (Customer: {item['doc'].get('user_name') or item['doc'].get('name')})")
            print(f"RAW DOC: {item['doc']}")
            missing_invoices += 1
        else:
            # Check for transaction
            transaction = await primary_engine.find_one(Transaction, Transaction.booking_id == booking_id)
            if not transaction:
                print(f"⚠️  MISSING TRANSACTION: [{item['type']}] Booking {booking_id} (Invoice {invoice.invoice_number} found, but no transaction)")
                missing_transactions += 1
            else:
                print(f"✅ OK: Booking {booking_id} has Invoice {invoice.invoice_number} and Transaction.")

    print(f"\n--- Final Results ---")
    print(f"Total Completed: {len(all_completed)}")
    print(f"Missing Invoices: {missing_invoices}")
    print(f"Missing Transactions: {missing_transactions}")

if __name__ == "__main__":
    asyncio.run(investigate_missing_invoices())
