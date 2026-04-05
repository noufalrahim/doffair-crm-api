import asyncio
import os
import sys
from datetime import datetime
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

# Add current directory to path to import local modules
sys.path.append(os.path.join(os.getcwd(), "doffair-python-vendor"))

try:
    from doffair_python_vendor.notifications.models.notification import InAppNotification
    from doffair_python_vendor.core.config import settings
except ImportError:
    # Fallback for different path structure
    try:
        from notifications.models.notification import InAppNotification
        from core.config import settings
    except ImportError:
        print("❌ Could not import models. Please run this script from the root of doffair-python-vendor")
        sys.exit(1)

async def verify_notifications():
    print("🔍 Starting Notification System Verification...")
    
    # Initialize engine
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    # 1. Create a dummy notification (Simulating Java behavior)
    test_user_id = "test_vendor_user_123"
    test_booking_id = "BK_TEST_999"
    
    print(f"📝 Creating test notification for user: {test_user_id}")
    notification = InAppNotification(
        user_id=test_user_id,
        vendor_id="test_vendor_456",
        title="Test Booking Alert",
        message="A new test booking has been created for verification.",
        notification_type="booking_create",
        reference_type="BOOKING",
        reference_id=test_booking_id,
        data={"event": "create", "test_mode": True},
        is_read=False,
        created_at=datetime.utcnow()
    )
    
    await engine.save(notification)
    print(f"✅ Notification saved to MongoDB (ID: {notification.id})")
    
    # 2. Verify retrieval
    print(f"📖 Verifying retrieval for user: {test_user_id}")
    fetched = await engine.find_one(InAppNotification, InAppNotification.user_id == test_user_id)
    
    if fetched:
        print(f"✅ Successfully retrieved notification: {fetched.title}")
        print(f"📊 Notification Type: {fetched.notification_type}")
        print(f"🔗 Reference ID: {fetched.reference_id}")
        print(f"💾 Metadata (data): {fetched.data}")
    else:
        print("❌ Failed to retrieve the notification from database!")
        return

    # 3. Cleanup
    print("🧹 Cleaning up test data...")
    # await engine.delete(fetched) # Uncomment to delete after test
    print("✅ Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_notifications())
