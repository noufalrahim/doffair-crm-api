"""
Show Vendor Details - Helper Script
Shows vendor_id and credentials for testing
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor import Vendor
from core.enums import VendorStatus

async def show_vendor_details():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    try:
        vendors = await engine.find(
            Vendor,
            (Vendor.status == VendorStatus.APPROVED) | (Vendor.status == VendorStatus.PRICING_CONFIGURED)
        )
        
        print("\n" + "="*60)
        print("📋 AVAILABLE VENDORS FOR TESTING")
        print("="*60 + "\n")
        
        for vendor in vendors:
            print(f"Vendor: {vendor.legal_name}")
            print(f"  ID: {str(vendor.id)}")
            print(f"  Phone: {vendor.primary_contact_phone}")
            print(f"  Email: {vendor.primary_contact_email}")
            print(f"  Status: {vendor.status}")
            print("-" * 60)
        
        if not vendors:
            print("❌ No approved vendors found")
            
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(show_vendor_details())
