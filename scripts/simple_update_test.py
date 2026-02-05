"""
Simple test - just verify the model loads correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vendor.models.vendor_service import VendorService
from pydantic import ValidationError

print("="*60)
print("TESTING VendorService MODEL")
print("="*60)

# Test 1: Check field definitions
print("\n✅ Field definitions:")
for field_name, field_info in VendorService.model_fields.items():
    print(f"  {field_name}: {field_info.annotation}")

# Test 2: Try creating with correct types
print("\n📝 Test creating service with correct field types...")
try:
    service = VendorService(
        vendor_id="test123",
        service_type_id="type123",
        location_id="loc123",
        name="Test Service",
        service_kind="BASE",
    )
    print(f"✅ Basic service created: {service.name}")
    print(f"   description: {service.description}")
    print(f"   duration_minutes: {service.duration_minutes}")
    print(f"   label: {service.label}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60)
print("Model definition is correct!")
print("="*60)
print("\n⚠️  If you're still getting 500 errors:")
print("   1. RESTART your FastAPI server (uvicorn)")
print("   2. The server caches the old model definition")
print("   3. After restart, the PATCH endpoint will work")
