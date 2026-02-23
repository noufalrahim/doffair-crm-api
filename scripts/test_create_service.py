import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor_service import VendorService
from vendor.schemas.service import BaseServiceCreateRequest
from vendor.services.service_service import create_base_service
from core.enums import ServiceDeliveryMode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_create_service():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    try:
        print("🔍 Starting service creation test...")
        
        # Find a vendor and location/vertical to use
        service = await engine.find_one(VendorService)
        if not service:
            print("❌ No service found to get vendor/location/vertical context")
            return
            
        vendor_id = service.vendor_id
        location_id = service.location_id
        vertical_id = service.vertical_id
        
        print(f"✅ Using Context - Vendor: {vendor_id}, Location: {location_id}, Vertical: {vertical_id}")
        
        test_images = [
            "vendors/test/services/test1",
            "vendors/test/services/test2"
        ]
        
        payload = BaseServiceCreateRequest(
            location_id=location_id,
            vertical_id=vertical_id,
            name="Test Image Service",
            description="Testing image saving",
            duration_minutes=30,
            delivery_mode=ServiceDeliveryMode.CENTER,
            base_price=500.0,
            images=test_images
        )
        
        print("📝 Creating base service...")
        new_service = await create_base_service(engine, vendor_id, payload)
        
        print(f"✅ Service created with ID: {new_service.id}")
        print(f"🖼️ Saved images: {new_service.images}")
        
        if new_service.images == test_images:
            print("🎉 SUCCESS: Images correctly saved!")
        else:
            print(f"❌ FAILURE: Images mismatch. Expected {test_images}, got {new_service.images}")
            
        # Cleanup
        await engine.delete(new_service)
        print("🧹 Cleanup: Deleted test service")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_create_service())
