# 🛠️ Utility Scripts

## Create Completed Booking

**Purpose**: Quickly create a completed booking for testing the invoice system without going through the entire booking flow.

### Usage

```bash
# From project root
python scripts/create_completed_booking.py
```

### What It Does

1. ✅ Finds or creates a Service Type
2. ✅ Finds or creates a Vendor (APPROVED status)
3. ✅ Creates a Vendor Location
4. ✅ Creates a Vendor Service
5. ✅ Creates Service Pricing
6. ✅ Finds or creates a User
7. ✅ Creates a Booking
8. ✅ Approves the Booking
9. ✅ **Marks Booking as COMPLETED**
10. ✅ Returns booking_id ready for invoice testing

### Output

```
🎉 COMPLETED BOOKING CREATED SUCCESSFULLY!
============================================================

📋 BOOKING DETAILS:
   Booking ID: 679abc123def456...
   Customer: Test User
   Vendor: Test Pet Salon
   Service: Basic Grooming Package
   Amount: ₹450.0
   Status: COMPLETED

🧾 NOW YOU CAN TEST INVOICE GENERATION:
   POST /vendor/invoices/generate
   {
     "booking_id": "679abc123def456...",
     "due_days": 30,
     "auto_send": true
   }

✅ Use this booking_id: 679abc123def456...
```

### Next Steps

1. Copy the booking_id from output
2. Go to Swagger UI: `http://localhost:8000/docs`
3. Navigate to "Vendor - Invoice Management"
4. Use `POST /vendor/invoices/generate`
5. Paste the booking_id and test!

### Requirements

- Database must be running
- MongoDB connection configured in `.env`
- Run from project root directory

### Notes

- Script is **idempotent** - can be run multiple times
- Reuses existing data when possible
- Creates minimal required data
- Safe for testing environments
