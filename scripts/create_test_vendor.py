"""
Create Test Vendor with Known Credentials
Creates a vendor account you can use for testing
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from core.enums import VendorStatus
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_vendor():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    try:
        print("\n" + "="*60)
        print("🏪 CREATING TEST VENDOR ACCOUNT")
        print("="*60 + "\n")
        
        # Test credentials
        test_email = "testvendor@example.com"
        test_phone = "+919876543210"
        test_password = "password123"
        
        # Check if vendor exists
        existing = await engine.find_one(
            Vendor,
            (Vendor.primary_contact_email == test_email) | (Vendor.primary_contact_phone == test_phone)
        )
        
        if existing:
            print(f"✅ Test vendor already exists!")
            print(f"   Email: {test_email}")
            print(f"   Phone: {test_phone}")
            print(f"   Password: {test_password}")
            print(f"   Vendor ID: {str(existing.id)}")
            print(f"   Status: {existing.status}")
            return str(existing.id)
        
        # Create vendor
        password_hash = pwd_context.hash(test_password)
        
        vendor = Vendor(
            primary_contact_email=test_email,
            primary_contact_phone=test_phone,
            password_hash=password_hash,
            legal_name="Test Pet Care Center",
            status=VendorStatus.APPROVED
        )
        
        await engine.save(vendor)
        vendor_id = str(vendor.id)
        
        print(f"✅ Vendor created successfully!")
        print(f"   Email: {test_email}")
        print(f"   Phone: {test_phone}")
        print(f"   Password: {test_password}")
        print(f"   Vendor ID: {vendor_id}")
        
        # Create location
        location = VendorLocation(
            vendor_id=vendor_id,
            name="Main Branch",
            address_line_1="123 Test Street",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            country="India",
            latitude=19.0760,
            longitude=72.8777,
            is_primary=True
        )
        await engine.save(location)
        
        print(f"✅ Location created: {location.name}")
        
        print("\n" + "="*60)
        print("🎉 TEST VENDOR READY!")
        print("="*60)
        print("\n📝 LOGIN CREDENTIALS:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print("\n🔐 Use these to login and get JWT token!")
        print("="*60 + "\n")
        
        return vendor_id
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_vendor())
