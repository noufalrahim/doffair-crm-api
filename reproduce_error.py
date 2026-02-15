
from vendor.models.vendor_service import VendorService
from core.enums import ServiceDeliveryMode
try:
    data = {
        "vendor_id": "123",
        "vertical_id": "456",
        "location_id": "789",
        "name": "Test Service",
        "service_kind": "BASE",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "duration_minutes": 30,
        "delivery_mode": "In-Center"
    }
    instance = VendorService.model_validate(data)
    print("Validation successful!")
    print(instance)
except Exception as e:
    print("Validation failed!")
    print(e)
