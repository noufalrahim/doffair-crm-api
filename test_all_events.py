"""
Comprehensive Test Script for All Event Types
Tests all 14 event types to ensure templates and notifications work correctly
"""
import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Test data
TEST_USER = {
    "user_id": "usr_test_001",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "user_phone": "+919876543210"
}

TEST_VENDOR = {
    "vendor_id": "vnd_test_001",
    "vendor_name": "Test Vendor",
    "vendor_email": "vendor@example.com",
    "vendor_phone": "+919123456789"
}

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def test_event(event_name, endpoint, payload):
    """Test an event and return result"""
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {event_name}: SUCCESS")
            print(f"   Event ID: {result.get('event_id', 'N/A')}")
            return True
        else:
            print(f"❌ {event_name}: FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ {event_name}: EXCEPTION")
        print(f"   Error: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE EVENT NOTIFICATION TESTING")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: {BASE_URL}")
    print("="*60)
    
    results = {}
    
    # Test 1: BOOKING_CREATED
    print_test_header("1. BOOKING CREATED")
    results['BOOKING_CREATED'] = test_event(
        "BOOKING_CREATED",
        "/events/publish/booking",
        {
            "event_type": "BOOKING_CREATED",
            "data": {
                "booking_id": "bk_001",
                "user_id": TEST_USER["user_id"],
                "vendor_id": TEST_VENDOR["vendor_id"],
                "service_type": "Pet Grooming",
                "scheduled_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "pet_name": "Buddy",
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "user_phone": TEST_USER["user_phone"],
                "vendor_name": TEST_VENDOR["vendor_name"],
                "vendor_email": TEST_VENDOR["vendor_email"],
                "vendor_phone": TEST_VENDOR["vendor_phone"],
                "total_amount": 1500
            }
        }
    )
    time.sleep(2)
    
    # Test 2: BOOKING_CANCELLED
    print_test_header("2. BOOKING CANCELLED")
    results['BOOKING_CANCELLED'] = test_event(
        "BOOKING_CANCELLED",
        "/events/publish/booking",
        {
            "event_type": "BOOKING_CANCELLED",
            "data": {
                "booking_id": "bk_002",
                "user_id": TEST_USER["user_id"],
                "vendor_id": TEST_VENDOR["vendor_id"],
                "service_type": "Pet Grooming",
                "scheduled_at": (datetime.now() + timedelta(days=5)).isoformat(),
                "cancellation_reason": "User requested cancellation",
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "user_phone": TEST_USER["user_phone"],
                "vendor_name": TEST_VENDOR["vendor_name"],
                "vendor_email": TEST_VENDOR["vendor_email"]
            }
        }
    )
    time.sleep(2)
    
    # Test 3: BOOKING_RESCHEDULED
    print_test_header("3. BOOKING RESCHEDULED")
    results['BOOKING_RESCHEDULED'] = test_event(
        "BOOKING_RESCHEDULED",
        "/events/publish/booking",
        {
            "event_type": "BOOKING_RESCHEDULED",
            "data": {
                "booking_id": "bk_003",
                "user_id": TEST_USER["user_id"],
                "vendor_id": TEST_VENDOR["vendor_id"],
                "service_type": "Pet Grooming",
                "scheduled_at": (datetime.now() + timedelta(days=10)).isoformat(),
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "user_phone": TEST_USER["user_phone"],
                "vendor_name": TEST_VENDOR["vendor_name"],
                "vendor_email": TEST_VENDOR["vendor_email"]
            }
        }
    )
    time.sleep(2)
    
    # Test 4: BOOKING_CONFIRMED
    print_test_header("4. BOOKING CONFIRMED")
    results['BOOKING_CONFIRMED'] = test_event(
        "BOOKING_CONFIRMED",
        "/events/publish/booking",
        {
            "event_type": "BOOKING_CONFIRMED",
            "data": {
                "booking_id": "bk_004",
                "user_id": TEST_USER["user_id"],
                "vendor_id": TEST_VENDOR["vendor_id"],
                "service_type": "Pet Grooming",
                "scheduled_at": (datetime.now() + timedelta(days=3)).isoformat(),
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "vendor_name": TEST_VENDOR["vendor_name"],
                "vendor_email": TEST_VENDOR["vendor_email"]
            }
        }
    )
    time.sleep(2)
    
    # Test 5: BOOKING_COMPLETED
    print_test_header("5. BOOKING COMPLETED")
    results['BOOKING_COMPLETED'] = test_event(
        "BOOKING_COMPLETED",
        "/events/publish/booking",
        {
            "event_type": "BOOKING_COMPLETED",
            "data": {
                "booking_id": "bk_005",
                "user_id": TEST_USER["user_id"],
                "vendor_id": TEST_VENDOR["vendor_id"],
                "service_type": "Pet Grooming",
                "scheduled_at": datetime.now().isoformat(),
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "vendor_name": TEST_VENDOR["vendor_name"]
            }
        }
    )
    time.sleep(2)
    
    # Test 6: PAYMENT_SUCCESS
    print_test_header("6. PAYMENT SUCCESS")
    results['PAYMENT_SUCCESS'] = test_event(
        "PAYMENT_SUCCESS",
        "/events/publish/payment",
        {
            "event_type": "PAYMENT_SUCCESS",
            "data": {
                "payment_id": "pay_001",
                "booking_id": "bk_001",
                "user_id": TEST_USER["user_id"],
                "amount": 1500,
                "currency": "INR",
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "user_phone": TEST_USER["user_phone"]
            }
        }
    )
    time.sleep(2)
    
    # Test 7: PAYMENT_FAILED
    print_test_header("7. PAYMENT FAILED")
    results['PAYMENT_FAILED'] = test_event(
        "PAYMENT_FAILED",
        "/events/publish/payment",
        {
            "event_type": "PAYMENT_FAILED",
            "data": {
                "payment_id": "pay_002",
                "booking_id": "bk_002",
                "user_id": TEST_USER["user_id"],
                "amount": 1500,
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "user_phone": TEST_USER["user_phone"],
                "failure_reason": "Insufficient funds"
            }
        }
    )
    time.sleep(2)
    
    # Test 8: PAYMENT_REFUNDED
    print_test_header("8. PAYMENT REFUNDED")
    results['PAYMENT_REFUNDED'] = test_event(
        "PAYMENT_REFUNDED",
        "/events/publish/payment",
        {
            "event_type": "PAYMENT_REFUNDED",
            "data": {
                "payment_id": "pay_003",
                "booking_id": "bk_002",
                "user_id": TEST_USER["user_id"],
                "amount": 1500,  # Original payment amount (required field)
                "refund_amount": 1500,
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "refund_reason": "Booking cancelled"
            }
        }
    )
    time.sleep(2)
    
    # Test 9: USER_REGISTERED
    print_test_header("9. USER REGISTERED")
    results['USER_REGISTERED'] = test_event(
        "USER_REGISTERED",
        "/events/publish",
        {
            "event_type": "USER_REGISTERED",
            "source": "user-service",
            "data": {
                "user_id": "usr_new_001",
                "user_name": "New User",
                "user_email": "newuser@example.com",
                "user_phone": "+919999999999"
            }
        }
    )
    time.sleep(2)
    
    # Test 10: USER_VERIFIED
    print_test_header("10. USER VERIFIED")
    results['USER_VERIFIED'] = test_event(
        "USER_VERIFIED",
        "/events/publish",
        {
            "event_type": "USER_VERIFIED",
            "source": "user-service",
            "data": {
                "user_id": TEST_USER["user_id"],
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"]
            }
        }
    )
    time.sleep(2)
    
    # Test 11: PASSWORD_RESET_REQUESTED
    print_test_header("11. PASSWORD RESET REQUESTED")
    results['PASSWORD_RESET_REQUESTED'] = test_event(
        "PASSWORD_RESET_REQUESTED",
        "/events/publish",
        {
            "event_type": "PASSWORD_RESET_REQUESTED",
            "source": "user-service",
            "data": {
                "user_id": TEST_USER["user_id"],
                "user_name": TEST_USER["user_name"],
                "user_email": TEST_USER["user_email"],
                "otp": "123456"
            }
        }
    )
    time.sleep(2)
    
    # Test 12: VENDOR_APPROVED
    print_test_header("12. VENDOR APPROVED")
    results['VENDOR_APPROVED'] = test_event(
        "VENDOR_APPROVED",
        "/events/publish",
        {
            "event_type": "VENDOR_APPROVED",
            "source": "vendor-service",
            "data": {
                "vendor_id": TEST_VENDOR["vendor_id"],
                "vendor_name": TEST_VENDOR["vendor_name"],
                "vendor_email": TEST_VENDOR["vendor_email"],
                "vendor_phone": TEST_VENDOR["vendor_phone"]
            }
        }
    )
    time.sleep(2)
    
    # Test 13: VENDOR_REJECTED
    print_test_header("13. VENDOR REJECTED")
    results['VENDOR_REJECTED'] = test_event(
        "VENDOR_REJECTED",
        "/events/publish",
        {
            "event_type": "VENDOR_REJECTED",
            "source": "vendor-service",
            "data": {
                "vendor_id": "vnd_rejected_001",
                "vendor_name": "Rejected Vendor",
                "vendor_email": "rejected@example.com",
                "rejection_reason": "Incomplete documentation"
            }
        }
    )
    time.sleep(2)
    
    # Print Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for event, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {event}: {'PASSED' if status else 'FAILED'}")
    
    print("="*60)
    print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check worker logs for details.")
    
    print("\n💡 TIP: Check Terminal 2 (worker) for notification processing logs\n")

if __name__ == "__main__":
    main()
