import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor import Vendor
from vendor.schemas.onboarding import VendorBasicInfoRequest
from vendor.services.onboarding_service import update_basic_info
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_update_basic_info():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    try:
        print("🔍 Starting basic info update test...")
        
        # Find a vendor to use
        vendor = await engine.find_one(Vendor)
        if not vendor:
            print("❌ No vendor found to test")
            return
            
        vendor_id = str(vendor.id)
        print(f"✅ Using Vendor ID: {vendor_id}")
        
        test_profile_image = "https://example.com/profile.jpg"
        test_cover_photo = "https://example.com/cover.jpg"
        
        payload = VendorBasicInfoRequest(
            legal_name=vendor.legal_name or "Test Vendor Name",
            gst_number=vendor.gst_number,
            business_registration_number=vendor.business_registration_number,
            profileImage=test_profile_image,
            coverPhoto=test_cover_photo
        )
        
        print("📝 Updating basic info...")
        updated_vendor = await update_basic_info(engine, vendor_id, payload)
        
        print(f"✅ Basic info updated for Vendor ID: {updated_vendor.id}")
        print(f"🖼️ Profile Image: {updated_vendor.profileImage}")
        print(f"🏞️ Cover Photo: {updated_vendor.coverPhoto}")
        
        if updated_vendor.profileImage == test_profile_image and updated_vendor.coverPhoto == test_cover_photo:
            print("🎉 SUCCESS: Basic info fields correctly saved!")
        else:
            print(f"❌ FAILURE: Field mismatch. Expected {test_profile_image} and {test_cover_photo}, got {updated_vendor.profileImage} and {updated_vendor.coverPhoto}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_update_basic_info())
