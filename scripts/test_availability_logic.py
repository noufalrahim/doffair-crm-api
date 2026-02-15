
from datetime import time
from vendor.services.availability_helper_service import get_slots_in_range, parse_time, format_time

def test_slot_splitting():
    print("Testing slot splitting...")
    start = time(9, 0)
    end = time(11, 0)
    slots = get_slots_in_range(start, end)
    
    for s in slots:
        print(f"Slot: {s.start_time} - {s.end_time}, Open: {s.is_open}")
    
    assert len(slots) == 4
    assert slots[0].start_time == "09:00 AM"
    assert slots[0].end_time == "09:30 AM"
    assert slots[-1].end_time == "11:00 AM"
    print("Slot splitting test passed!")

def test_time_parsing():
    print("\nTesting time parsing...")
    assert parse_time("09:00 AM") == time(9, 0)
    assert parse_time("09:00 PM") == time(21, 0)
    assert parse_time("14:30") == time(14, 30)
    print("Time parsing test passed!")

if __name__ == "__main__":
    try:
        test_slot_splitting()
        test_time_parsing()
    except Exception as e:
        print(f"Tests failed: {e}")
