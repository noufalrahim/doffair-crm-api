# Event-Driven Notification System - Testing Guide

## Overview
This guide will help you test the new event-driven notification system that sends notifications automatically when domain events occur (bookings, payments, user actions, etc.).

---

## Prerequisites

**Required Services:**
- Redis running on `localhost:6379`
- MongoDB running on `localhost:27017`
- Python 3.10+

**Check Services:**
```powershell
# Check Redis
redis-cli ping
# Should return: PONG

# Check MongoDB
mongosh --eval "db.runCommand({ ping: 1 })"
# Should return: ok: 1
```

---

## Step 1: Environment Setup

Copy `.env.example` to `.env` and configure:

```env
# Minimal configuration for testing (mock mode)
REDIS_URL=redis://localhost:6379/0
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=doffair_dev

# Leave these empty for mock mode (no real notifications sent)
SMTP_USERNAME=
SMTP_PASSWORD=
TWOFACTOR_API_KEY=
```

**Mock Mode**: With empty credentials, the system logs notifications but doesn't send real emails/SMS. Perfect for testing!

---

## Step 2: Start the FastAPI Server

**Terminal 1:**
```powershell
cd doffair-python-vendor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify**: Open http://localhost:8000/docs

---

## Step 3: Start the Worker

**Terminal 2:**
```powershell
cd doffair-python-vendor
python run_worker.py
```

**Expected Output:**
```
🚀 Starting Notification Worker
📡 Redis URL: redis://localhost:6379/0
📋 Queue Name: doffair:notifications
*** Listening on doffair:notifications...
```

Keep this running throughout testing.

---

## Step 4: Testing via Swagger UI

### Overview of Available Routes

Open http://localhost:8000/docs to access Swagger UI. You'll see these event-related endpoints:

1. **POST /events/publish** - Publish any generic event
2. **POST /events/publish/booking** - Publish booking-specific events
3. **POST /events/publish/payment** - Publish payment-specific events
4. **GET /events/queue/info** - Check queue status

### Test 1: Publish Booking Event (BOOKING_CREATED)

**Route:** `POST /events/publish/booking`

**What it does:** Creates a new booking and sends notifications to both user and vendor via Email, SMS, and In-App.

**Steps:**
1. Open http://localhost:8000/docs
2. Find `POST /events/publish/booking`
3. Click "Try it out"
4. Paste this payload:

```json
{
  "event_type": "BOOKING_CREATED",
  "data": {
    "booking_id": "bk_123",
    "user_id": "usr_test_001",
    "vendor_id": "vnd_test_001",
    "vertical": "Pet Grooming",
    "scheduled_at": "2026-02-01T14:00:00",
    "pet_name": "Buddy",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "user_phone": "+919876543210",
    "vendor_name": "Test Vendor",
    "vendor_email": "vendor@example.com",
    "vendor_phone": "+919123456789",
    "total_amount": 1500
  }
}
```

5. Click "Execute"
6. **Watch Terminal 2 (Worker)** - you'll see:
```
📨 Processing event: evt_...
📧 [MOCK] Would send email to test@example.com
📱 [MOCK] Would send SMS to +919876543210
📧 [MOCK] Would send email to vendor@example.com
📱 [MOCK] Would send SMS to +919876543210
✅ Event processed: 6/6 notifications sent
```

**Note:** You'll see 4 log lines (2 emails + 2 SMS) but the system actually sends **6 notifications** (2 emails + 2 SMS + 2 in-app). In-app notifications are created silently in MongoDB without individual log lines in mock mode.

**Success Response (in Swagger):**
```json
{
  "success": true,
  "event_id": "evt_...",
  "message": "Booking event published successfully"
}
```

### Test 2: Publish Booking Cancellation

**Route:** `POST /events/publish/booking`

**What it does:** Notifies user and vendor about booking cancellation.

**Payload:**
```json
{
  "event_type": "BOOKING_CANCELLED",
  "data": {
    "booking_id": "bk_456",
    "user_id": "usr_test_001",
    "vendor_id": "vnd_test_001",
    "vertical": "Pet Grooming",
    "scheduled_at": "2026-02-01T14:00:00",
    "cancellation_reason": "User requested cancellation",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "user_phone": "+919876543210",
    "vendor_name": "Test Vendor",
    "vendor_email": "vendor@example.com"
  }
}
```

### Test 3: Publish Payment Success

**Route:** `POST /events/publish/payment`

**What it does:** Notifies user about successful payment via Email, SMS, and In-App.

**Payload:

```json
{
  "event_type": "PAYMENT_SUCCESS",
  "data": {
    "payment_id": "pay_123",
    "booking_id": "bk_123",
    "user_id": "usr_test_001",
    "amount": 1500,
    "currency": "INR",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "user_phone": "+919876543210"
  }
}
```

**Expected Worker Output:**
```
📨 Processing event: evt_...
📧 [MOCK] Would send email to test@example.com
📱 [MOCK] Would send SMS to +919876543210
✅ Event processed: 3/3 notifications sent
```

**Note:** In-app notifications are created silently in the database. You won't see a separate log line for them in mock mode, but they are being saved to MongoDB. Verify by checking MongoDB (see Step 5 below).

### Test 4: Publish Generic Event

**Route:** `POST /events/publish`

**What it does:** Publish any event type with custom data.

**Example - User Registration:**
```json
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
```

**Important:** The `source` field must use **hyphens** not underscores:
- ✅ `"user-service"` (correct)
- ❌ `"user_service"` (wrong - will cause 422 error)

**Important:** If you get a **422 error** in Swagger, the JSON might have formatting issues. Try this instead:

**Using PowerShell (more reliable):**
```powershell
cd doffair-python-vendor
curl -X POST http://localhost:8000/events/publish -H "Content-Type: application/json" -d "@test_generic_event.json"
```

This uses the pre-formatted `test_generic_event.json` file which has correct formatting.

### Test 5: Check Queue Status

**Route:** `GET /events/queue/info`

**What it does:** Shows Redis queue status and pending jobs.

**Steps:**
1. Find `GET /events/queue/info`
2. Click "Try it out" → "Execute"

**Response:**
```json
{
  "queue_name": "doffair:notifications",
  "pending_jobs": 0,
  "redis_connected": true
}
```

**Note:** `pending_jobs` shows how many events are waiting to be processed. If worker is running, this should be 0 (events process instantly).

---

## Understanding Notification Channels

### Why am I seeing Email and SMS but not WhatsApp?

The notification system is **configurable** - each event type can send to different channels based on `routing.json`.

**Current Configuration:**
- ✅ **Email** - Enabled for most events
- ✅ **SMS** - Enabled for high-priority events (bookings, payments)
- ✅ **In-App** - Enabled for all events
- ❌ **WhatsApp** - Currently NOT configured (but ready to use!)

**To Enable WhatsApp:**

1. Add WhatsApp to desired events in `notifications/config/routing.json`:
```json
{
  "BOOKING_CREATED": {
    "recipients": ["user", "vendor"],
    "channels": {
      "user": ["email", "in_app", "sms", "whatsapp"],
      "vendor": ["email", "in_app", "sms", "whatsapp"]
    },
    "priority": "high"
  }
}
```

2. Add Twilio credentials to `.env`:
```env
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

3. Restart worker → WhatsApp notifications will be sent!

**Mock Mode:**
Without Twilio credentials, WhatsApp will log like Email/SMS:
```
💬 [MOCK] Would send WhatsApp to +919876543210
```

---

## Step 5: Verify In-App Notifications

Check MongoDB to see created notifications:

```javascript
// Connect to MongoDB
mongosh

// Switch to database
use doffair_dev

// View notifications
db.inapp_notifications.find().sort({created_at: -1}).limit(5).pretty()
```

**Expected:**
```json
{
  "_id": "...",
  "user_id": "usr_test_001",
  "title": "Booking Confirmed",
  "message": "Booking confirmed! Pet Grooming for Buddy on 2026-02-01...",
  "notification_type": "BOOKING_CREATED",
  "is_read": false,
  "created_at": "2026-01-27T12:00:00Z"
}
```

---

## Supported Event Types

The system supports these events:

### Booking Events
- `BOOKING_CREATED` - New booking made
- `BOOKING_CANCELLED` - Booking cancelled
- `BOOKING_RESCHEDULED` - Booking time changed
- `BOOKING_CONFIRMED` - Vendor confirmed
- `BOOKING_COMPLETED` - Service completed

### Payment Events
- `PAYMENT_SUCCESS` - Payment successful
- `PAYMENT_FAILED` - Payment failed
- `PAYMENT_REFUNDED` - Refund processed

### User Events
- `USER_REGISTERED` - New user signup
- `USER_VERIFIED` - Email verified
- `PASSWORD_RESET_REQUESTED` - Password reset

### Vendor Events
- `VENDOR_APPROVED` - Application approved
- `VENDOR_REJECTED` - Application rejected

---

## Troubleshooting

### Worker Not Processing Events

**Check:**
1. Redis is running: `redis-cli ping`
2. Worker terminal shows "Listening on doffair:notifications"
3. No errors in worker logs

**Fix:**
```powershell
# Stop worker (Ctrl+C)
# Clear Python cache
Remove-Item -Recurse -Force __pycache__
# Restart worker
python run_worker.py
```

### Events Not Publishing

**Check:**
1. Server running: http://localhost:8000/docs
2. Check logs in Terminal 1 for errors
3. Verify Redis connection

### No Notifications Created

**Check:**
1. MongoDB is running
2. Check worker logs for errors
3. Verify event payload has all required fields

---

## Production Deployment

### Enable Real Notifications

Update `.env` with real credentials:

```env
# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@doffair.com
SMTP_FROM_NAME=Doffair

# SMS (2Factor)
TWOFACTOR_API_KEY=your-api-key

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Restart worker → Real notifications will be sent!

### Run Worker as Service

**Windows (using NSSM):**
```powershell
nssm install DoffairWorker "C:\path\to\python.exe" "C:\path\to\run_worker.py"
nssm start DoffairWorker
```

**Linux (systemd):**
```bash
sudo nano /etc/systemd/system/doffair-worker.service
```

```ini
[Unit]
Description=Doffair Notification Worker
After=network.target redis.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/doffair-python-vendor
ExecStart=/path/to/venv/bin/python run_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable doffair-worker
sudo systemctl start doffair-worker
```

---

## How to Integrate in Your Code

### Example: Booking Created

```python
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource

# After saving booking to database
event_publisher.publish(
    event_type=EventType.BOOKING_CREATED,
    data={
        "booking_id": str(booking.id),
        "user_id": str(booking.user_id),
        "vendor_id": str(booking.vendor_id),
        "service_type": booking.service.name,
        "scheduled_at": booking.scheduled_at.isoformat(),
        "pet_name": booking.pet.name,
        "user_name": booking.user.name,
        "user_email": booking.user.email,
        "user_phone": booking.user.phone,
        "vendor_name": booking.vendor.name,
        "vendor_email": booking.vendor.email,
        "vendor_phone": booking.vendor.phone,
        "total_amount": float(booking.total_amount)
    },
    source=EventSource.BOOKING_SERVICE
)
```

### Example: Payment Success

```python
event_publisher.publish(
    event_type=EventType.PAYMENT_SUCCESS,
    data={
        "payment_id": str(payment.id),
        "booking_id": str(payment.booking_id),
        "user_id": str(payment.user_id),
        "amount": float(payment.amount),
        "currency": "INR",
        "user_name": payment.user.name,
        "user_email": payment.user.email,
        "user_phone": payment.user.phone
    },
    source=EventSource.PAYMENT_SERVICE
)
```

---

## Testing Checklist

- [ ] Redis running
- [ ] MongoDB running
- [ ] Server started (Terminal 1)
- [ ] Worker started (Terminal 2)
- [ ] All Swagger tests work
- [ ] Manual Swagger test works
- [ ] Worker logs show processing
- [ ] In-app notifications in MongoDB
- [ ] Mock emails logged
- [ ] Mock SMS logged

---

## Architecture Overview

```
┌─────────────────┐
│  FastAPI App    │
│  (Your Code)    │
└────────┬────────┘
         │ publish()
         ▼
┌─────────────────┐
│  Event Publisher│
│   (Redis Queue) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RQ Worker      │  ← Terminal 2
│  (Background)   │
└────────┬────────┘
         │
         ├──► Email Handler (SMTP)
         ├──► SMS Handler (2Factor)
         ├──► WhatsApp Handler (Twilio)
         └──► In-App Handler (MongoDB)
```

---

## Support

If you encounter issues:
1. Check Redis is running
2. Check MongoDB is running
3. Clear Python cache
4. Restart worker
5. Check logs in both terminals

**Success Indicators:**
- ✅ Events publish instantly
- ✅ Worker processes immediately
- ✅ Notifications logged/created
- ✅ No errors in logs

---

## Summary

Your notification system is now:
- ✅ **Event-driven** - Fire and forget
- ✅ **Multi-channel** - Email, SMS, WhatsApp, In-App
- ✅ **Asynchronous** - Non-blocking
- ✅ **Scalable** - Redis queue handles load
- ✅ **Idempotent** - No duplicate notifications
- ✅ **Template-based** - Easy to customize
- ✅ **Production-ready** - Mock + Real modes

**Happy Testing! 🚀**
