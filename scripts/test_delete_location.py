import asyncio
import sys
from pathlib import Path
from bson import ObjectId
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor_location import VendorLocation
from vendor.models.care_professional import CareProfessional
from vendor.models.vendor_service import VendorService
from vendor.services.location_service import delete_location
from fastapi import HTTPException

async def test_delete_location():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    vendor_id = "test_vendor_id_123"
    
    try:
        print("🔍 Starting location deletion test...")

        # 1. Create two locations
        loc1 = VendorLocation(
            vendor_id=vendor_id,
            name="Test Location 1",
            address_line_1="Address 1",
            city="City 1",
            state="State 1",
            pincode="123456",
            latitude=0.0,
            longitude=0.0,
            is_default=True
        )
        loc2 = VendorLocation(
            vendor_id=vendor_id,
            name="Test Location 2",
            address_line_1="Address 2",
            city="City 2",
            state="State 2",
            pincode="654321",
            latitude=1.1,
            longitude=1.1,
            is_default=False
        )
        await engine.save_all([loc1, loc2])
        print(f"✅ Created two locations: {loc1.id} (default), {loc2.id}")

        # 2. Test staff blocking
        staff = CareProfessional(
            vendor_id=vendor_id,
            user_id="test_user_id",
            location_id=str(loc2.id),
            vertical_id="test_vertical",
            name="Test Staff",
            is_active=True
        )
        await engine.save(staff)
        print(f"✅ Created staff linked to {loc2.id}")

        try:
            await delete_location(engine, vendor_id, str(loc2.id))
            print("❌ FAILURE: Deleted location with active staff")
        except HTTPException as e:
            print(f"✅ Successfully blocked deletion with staff: {e.detail}")

        # Deactivate staff and try again
        staff.is_active = False
        await engine.save(staff)
        print(f"✅ Deactivated staff")
        
        await delete_location(engine, vendor_id, str(loc2.id))
        print(f"✅ Successfully deleted location {loc2.id} after staff deactivation")

        # 3. Test service blocking
        service = VendorService(
            vendor_id=vendor_id,
            location_id=str(loc1.id),
            vertical_id="test_vertical",
            name="Test Service",
            service_kind="test",
            is_active=True
        )
        await engine.save(service)
        print(f"✅ Created service linked to {loc1.id} (default)")

        try:
            await delete_location(engine, vendor_id, str(loc1.id))
            print("❌ FAILURE: Deleted location with active service")
        except HTTPException as e:
            print(f"✅ Successfully blocked deletion with service: {e.detail}")

        # Deactivate service and test default transfer
        service.is_active = False
        await engine.save(service)
        print(f"✅ Deactivated service")

        # Create one more location to transfer default to
        loc3 = VendorLocation(
            vendor_id=vendor_id,
            name="Test Location 3",
            address_line_1="Address 3",
            city="City 3",
            state="State 3",
            pincode="111222",
            latitude=2.2,
            longitude=2.2,
            is_default=False
        )
        await engine.save(loc3)
        print(f"✅ Created {loc3.id} as a backup for default")

        await delete_location(engine, vendor_id, str(loc1.id))
        print(f"✅ Successfully deleted default location {loc1.id}")

        # Check if loc3 became default
        updated_loc3 = await engine.find_one(VendorLocation, VendorLocation.id == loc3.id)
        if updated_loc3 and updated_loc3.is_default:
            print(f"✅ SUCCESS: Default status transferred to {loc3.id}")
        else:
            print(f"❌ FAILURE: Default status NOT transferred")

        # Cleanup
        await engine.delete(staff)
        await engine.delete(service)
        await engine.delete(updated_loc3)
        print("🧹 Cleanup: Deleted test records")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_delete_location())
