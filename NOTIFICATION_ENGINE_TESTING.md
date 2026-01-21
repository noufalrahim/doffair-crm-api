# Notification Engine - Complete Testing Guide

## 📋 Overview

This guide covers testing the complete asynchronous multi-channel notification engine that supports:
- **Email** notifications (SMTP)
- **SMS** notifications (2Factor API)
- **WhatsApp** notifications (Twilio)
- **In-App** notifications (MongoDB)

**Architecture**: Non-blocking API → Redis Queue → Background Workers → Multi-channel delivery

---

## 🔧 Prerequisites

### 1. System Requirements
- Python 3.10+
- Redis (Windows: Memurai recommended)
- MongoDB connection
- Virtual environment activated

### 2. Install Dependencies

```powershell
pip install redis==5.0.1 rq==1.16.0 aiohttp==3.9.1 aiosmtplib==3.0.1 jinja2==3.1.3
```

### 3. Environment Configuration

Add to your `.env` file:

```env
# Redis Configuration (Required)
REDIS_URL=redis://localhost:6379/0

# Email Settings (Optional - uses mock mode if not configured)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@doffair.com
SMTP_FROM_NAME=Doffair

# SMS Settings (Optional - uses mock mode if not configured)
TWOFACTOR_API_KEY=your_api_key_here
TWOFACTOR_OTP_TEMPLATE=DOFFAIR_OTP

# WhatsApp Settings (Optional - uses mock mode if not configured)
WHATSAPP_ACCOUNT_SID=
WHATSAPP_AUTH_TOKEN=
WHATSAPP_FROM_NUMBER=
```

**Note**: If credentials are empty or set to placeholder values, handlers run in **MOCK MODE** (perfect for testing).

---

## 🚀 Testing Steps

### Part 1: Start Services

#### Step 1.1: Verify Redis is Running

Test Redis connection:
```powershell
python test_redis.py
```

**Expected Output**:
```
✅ SUCCESS! Redis is running and accepting connections
   Host: localhost
   Port: 6379
```

If Redis is not running:
- **Windows**: Start Memurai service or run `redis-server.exe`
- **Docker**: `docker run -d -p 6379:6379 redis:latest`

---

#### Step 1.2: Start FastAPI Server (Terminal 1)

```powershell
uvicorn main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

✅ Server is running

---

### Part 2: Test Phase 1 (Queue Publisher)

#### Step 2.1: Check Queue Health

Open browser: `http://localhost:8000/docs`

**Endpoint**: `GET /notifications/queue/info`

Click "Try it out" → "Execute"

**Expected Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "health": "healthy",
    "queue": {
      "name": "doffair:notifications",
      "count": 0,
      "started_jobs": 0,
      "finished_jobs": 0,
      "failed_jobs": 0,
      "scheduled_jobs": 0
    }
  }
}
```

✅ Redis connection is healthy

---

#### Step 2.2: Send Test Notification

**Endpoint**: `POST /notifications/send`

**Request Body**:
```json
{
  "channels": ["email", "in_app"],
  "recipient": {
    "user_id": "test_user_123",
    "email": "test@example.com"
  },
  "template_id": "TEST_NOTIFICATION",
  "subject": "Test Notification",
  "message": "Testing the notification engine",
  "event_type": "test",
  "priority": "high"
}
```

**Expected Response** (202 Accepted):
```json
{
  "success": true,
  "success_message": "Notification request accepted and queued for processing",
  "data": {
    "notification_id": "696669199b397093c627839a",
    "status": "queued",
    "message": "Notification queued for processing",
    "queued_at": "2026-01-13T16:15:30.123456",
    "channels": ["email", "in_app"]
  }
}
```

**Success Indicators**:
- ✅ HTTP Status: **202 Accepted** (not 200, not 500)
- ✅ Response time < 100ms (non-blocking)
- ✅ Returns `notification_id`
- ✅ Status is `"queued"`

📝 **Copy the `notification_id`** for next step

---

#### Step 2.3: Verify Notification Queued

**Endpoint**: `GET /notifications/queue/info`

**Expected Response**:
```json
{
  "queue": {
    "count": 1,  ← One job waiting for worker
    "started_jobs": 0,
    "finished_jobs": 0
  }
}
```

✅ Notification is queued

---

#### Step 2.4: Check Notification Status

**Endpoint**: `GET /notifications/status/{notification_id}`

Replace `{notification_id}` with the ID from Step 2.2

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "notification_id": "696669199b397093c627839a",
    "status": "queued",
    "channels": ["email", "in_app"],
    "channel_status": {
      "email": "pending",
      "in_app": "pending"
    },
    "created_at": "2026-01-13T16:15:30.123456",
    "sent_at": null,
    "retry_count": 0,
    "error_message": null
  }
}
```

✅ Status is `"queued"`, channels show `"pending"`

---

## ✅ Phase 1 Complete

**Verified**:
- ✅ API accepts notifications
- ✅ Validates request payload
- ✅ Creates MongoDB records
- ✅ Queues jobs to Redis
- ✅ Returns immediately (non-blocking)
- ✅ Can check notification status

---

### Part 3: Test Phase 2 (Workers & Delivery)

#### Step 3.1: Start Worker (Terminal 2)

Open a **new PowerShell terminal** (keep Terminal 1 running):

```powershell
python run_worker.py
```

**Expected Output**:
```
============================================================
🚀 Starting Notification Worker
============================================================
📡 Redis URL: redis://localhost:6379/0
📋 Queue Name: doffair:notifications
⏰ Listening for jobs... (Press Ctrl+C to quit)
============================================================

Worker rq:worker:... started with PID ...
*** Listening on doffair:notifications...
```

✅ Worker is listening

---

#### Step 3.2: Watch Worker Process Notification

**Immediately**, the worker should pick up the queued notification:

**Expected Terminal 2 Output**:
```
🔄 Processing notification 696669199b397093c627839a
📤 Sending through channels: ['email', 'in_app']
📧 [MOCK] Would send email to test@example.com
   Subject: Test Notification
   Body: Testing the notification engine
✅ email: Email sent to test@example.com
✅ [inapp] Notification 696669199b397093c627839a sent successfully
✅ in_app: In-app notification created successfully
✅ Notification 696669199b397093c627839a sent successfully through all channels
Job OK
```

**Success Indicators**:
- ✅ Shows "Processing notification"
- ✅ Both channels show ✅ (email and in_app)
- ✅ Says "sent successfully through all channels"
- ✅ "Job OK"
- ✅ No errors

**Note**: Email shows `[MOCK]` because credentials aren't configured - this is expected!

---

#### Step 3.3: Verify Status Changed to "sent"

In Swagger: `GET /notifications/status/{notification_id}`

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "notification_id": "696669199b397093c627839a",
    "status": "sent",    ← Changed from "queued"!
    "channels": ["email", "in_app"],
    "channel_status": {
      "email": "sent",   ← Changed from "pending"!
      "in_app": "sent"  ← Changed from "pending"!
    },
    "created_at": "2026-01-13T16:15:30.123456",
    "sent_at": "2026-01-13T16:15:32.456789",  ← Now has timestamp!
    "retry_count": 0,
    "error_message": null
  }
}
```

✅ Status updated to `"sent"`, all channels show `"sent"`

---

#### Step 3.4: Verify Queue is Empty

In Swagger: `GET /notifications/queue/info`

**Expected Response**:
```json
{
  "queue": {
    "count": 0,           ← Back to 0!
    "started_jobs": 0,
    "finished_jobs": 1,  ← 1 job completed!
    "failed_jobs": 0
  }
}
```

✅ Worker processed the job, queue is empty

---

### Part 4: Test All 4 Channels

#### Step 4.1: Send Multi-Channel Notification

**Keep worker running** in Terminal 2

In Swagger: `POST /notifications/send`

```json
{
  "channels": ["email", "sms", "whatsapp", "in_app"],
  "recipient": {
    "user_id": "test_user_456",
    "email": "user@example.com",
    "phone": "+919876543210",
    "whatsapp": "+919876543210"
  },
  "template_id": "MULTI_CHANNEL_TEST",
  "subject": "Testing All 4 Channels",
  "message": "This notification goes through all channels!",
  "event_type": "test"
}
```

**Expected Response**: `202 Accepted` with notification_id

---

#### Step 4.2: Watch Worker Process All Channels

**Expected Terminal 2 Output**:
```
🔄 Processing notification...
📤 Sending through channels: ['email', 'sms', 'whatsapp', 'in_app']
📧 [MOCK] Would send email to user@example.com
   Subject: Testing All 4 Channels
   Body: This notification goes through all channels!
✅ email: Email sent to user@example.com
📱 [MOCK] Would send SMS to +919876543210
   Message: This notification goes through all channels!
✅ sms: SMS sent to +919876543210
💬 [MOCK] Would send WhatsApp to whatsapp:+919876543210
   Message: This notification goes through all channels!
✅ whatsapp: WhatsApp sent to whatsapp:+919876543210
✅ [inapp] Notification ... sent successfully
✅ in_app: In-app notification created successfully
✅ Notification ... sent successfully through all channels
Job OK
```

**Success Indicators**:
- ✅ All 4 channels show ✅
- ✅ Email, SMS, WhatsApp in MOCK mode
- ✅ In-app creates actual MongoDB record
- ✅ "Job OK"

---

#### Step 4.3: Verify All Channels Sent

In Swagger: `GET /notifications/status/{notification_id}`

**Expected Response**:
```json
{
  "status": "sent",
  "channel_status": {
    "email": "sent",
    "sms": "sent",
    "whatsapp": "sent",
    "in_app": "sent"
  },
  "sent_at": "2026-01-13T..."
}
```

✅ All 4 channels successfully delivered

---

## ✅ Phase 2 Complete - All Tests Passed

**Verified**:
- ✅ Worker starts without errors
- ✅ Worker picks up queued jobs (< 1 second)
- ✅ Email handler works (MOCK mode)
- ✅ SMS handler works (MOCK mode)
- ✅ WhatsApp handler works (MOCK mode)
- ✅ In-App handler creates DB records
- ✅ Status updates to "sent" after processing
- ✅ All channels show "sent" status
- ✅ Queue count returns to 0 after processing
- ✅ No errors in worker logs

---

## 🎯 Test Scenarios

### Scenario 1: Test Without Worker Running

1. Stop worker (Ctrl+C in Terminal 2)
2. Send notification via Swagger
3. Check queue: Should show `count: 1`
4. Check status: Should show `"queued"`
5. Start worker: It immediately processes the job

**Proves**: Notifications queue even when worker is offline ✅

---

### Scenario 2: Test Validation Errors

**Missing required field**:

```json
{
  "channels": ["email"],
  "recipient": {
    "user_id": "test"
    // Missing email!
  },
  "subject": "Test"
}
```

**Expected**: `400 Bad Request` with validation error ✅

---

### Scenario 3: Check MongoDB Records

After sending notifications, check MongoDB:

**Collection**: `notification_logs`

Should contain documents with:
- `status: "sent"`
- `channels: ["email", "in_app"]`
- `channel_status: {email: "sent", in_app: "sent"}`
- `sent_at: ISODate(...)`

**Collection**: `in_app_notifications`

Should contain in-app notification records with:
- `user_id`
- `title`, `message`
- `is_read: false`
- `created_at`

✅ Data persisted correctly

---

## 📊 What's Happening Behind the Scenes

```
1. Client sends POST /notifications/send
   ↓
2. API validates payload (5ms)
   ↓
3. Creates NotificationLog in MongoDB (20ms)
   ↓
4. Pushes job to Redis queue (5ms)
   ↓
5. Returns 202 Accepted (30ms total) ← API DONE!
   ↓
6. Worker picks up job from Redis (< 1 second)
   ↓
7. Worker sends through each channel:
   - Email: SMTP/mock
   - SMS: 2Factor API/mock
   - WhatsApp: Twilio API/mock
   - In-App: MongoDB insert
   ↓
8. Worker updates status to "sent" in MongoDB
   ↓
9. Job marked complete in Redis
```

---

## 🔧 Troubleshooting

### Issue: Queue shows "unhealthy"

**Cause**: Redis not running

**Solution**:
- Windows: Start Memurai service
- Docker: `docker run -d -p 6379:6379 redis:latest`
- Test: `python test_redis.py`

---

### Issue: Worker crashes with SIGALRM error

**Cause**: Windows doesn't support SIGALRM signal

**Solution**: Already fixed! Worker uses `WindowsDeathPenalty` class that's Windows-compatible.

---

### Issue: Datetime validation errors

**Cause**: ODMantic/Pydantic datetime validation

**Solution**: Already fixed! Uses MongoDB `update_one()` directly to bypass validation.

---

### Issue: Worker doesn't pick up jobs

**Check**:
1. Worker is running (Terminal 2 shows "Listening...")
2. Redis URL matches in `.env`: `REDIS_URL=redis://localhost:6379/0`
3. Queue name matches: `REDIS_QUEUE_NAME=doffair:notifications`
4. Check queue has jobs: `GET /notifications/queue/info`

**Solution**: Restart worker (Ctrl+C then start again)

---

### Issue: SMS/Email shows actual API errors instead of MOCK

**Cause**: API key is set but invalid

**Solution**: Set to empty string or `"your_api_key_here"` to force MOCK mode

---

## 🚀 Production Deployment

### Add Real Credentials

Update `.env` with real API credentials:

```env
# Email (Gmail example)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS (2Factor)
TWOFACTOR_API_KEY=abc123def456

# WhatsApp (Twilio)
WHATSAPP_ACCOUNT_SID=ACxxxxxxxxxxxx
WHATSAPP_AUTH_TOKEN=your_auth_token
WHATSAPP_FROM_NUMBER=whatsapp:+14155238886
```

Once configured, notifications will be sent through real APIs!

---

### Run Worker as Service

**Windows (using NSSM)**:
```powershell
nssm install DoffairNotificationWorker "C:\path\to\venv\Scripts\python.exe" "C:\path\to\run_worker.py"
nssm start DoffairNotificationWorker
```

**Linux (systemd)**:
```ini
[Unit]
Description=Doffair Notification Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/app
ExecStart=/path/to/venv/bin/python run_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Scale Workers

Run multiple worker instances for high throughput:

```powershell
# Terminal 2
python run_worker.py

# Terminal 3
python run_worker.py

# Terminal 4
python run_worker.py
```

All workers share the same Redis queue. Jobs are distributed automatically.

---

## 📝 Integration Example

### Booking Confirmation Notification

```python
import requests

def send_booking_confirmation(booking):
    """Send notification when booking is confirmed"""
    
    response = requests.post(
        'http://localhost:8000/notifications/send',
        json={
            "channels": ["email", "sms", "in_app"],
            "recipient": {
                "user_id": str(booking.user_id),
                "email": booking.user_email,
                "phone": booking.user_phone
            },
            "template_id": "BOOKING_CONFIRMED",
            "subject": "Your booking is confirmed!",
            "data": {
                "booking_id": str(booking.id),
                "service_name": booking.service_name,
                "booking_date": booking.date.isoformat(),
                "vendor_name": booking.vendor_name,
                "amount": str(booking.amount)
            },
            "event_type": "booking",
            "priority": "high",
            "reference_type": "booking",
            "reference_id": str(booking.id)
        },
        timeout=5
    )
    
    if response.status_code == 202:
        print(f"Notification queued: {response.json()['data']['notification_id']}")
    else:
        print(f"Failed to queue notification: {response.text}")
```

**API returns immediately** - notifications sent in background! ⚡

---

## 🎉 Success Criteria

✅ **API Performance**
- POST /notifications/send responds in < 100ms
- Returns 202 Accepted (not 200 or 500)
- Non-blocking operation

✅ **Queue Functionality**
- Jobs queued to Redis successfully
- Queue health check returns "healthy"
- Queue count increases/decreases correctly

✅ **Worker Processing**
- Worker starts without errors
- Picks up jobs within 1 second
- Processes all requested channels
- Updates status to "sent" after completion

✅ **Channel Delivery**
- Email: Logs sent (mock) or delivers (real SMTP)
- SMS: Logs sent (mock) or delivers (2Factor API)
- WhatsApp: Logs sent (mock) or delivers (Twilio)
- In-App: Creates MongoDB record

✅ **Error Handling**
- Validation errors return 400 with details
- Failed channels don't block others
- Automatic retry on transient failures
- Status tracks per-channel results

✅ **Data Persistence**
- notification_logs collection updated
- in_app_notifications collection created
- Status and timestamps accurate

---

## 📚 API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/send` | POST | Send notification (queues for processing) |
| `/notifications/status/{id}` | GET | Check notification status |
| `/notifications/queue/info` | GET | Get queue health and stats |
| `/notifications/user/{user_id}/in-app` | GET | Get user's in-app notifications |
| `/notifications/in-app/{id}/read` | PUT | Mark in-app notification as read |

---

## 🔗 Related Documentation

- **Architecture Diagram**: See project README
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Configuration Guide**: See `.env.example`
- **Channel Handler Details**: See `notifications/handlers/` source code

---

## ✨ Testing Complete!

You've successfully tested a production-ready, scalable, asynchronous multi-channel notification engine.

**Features Verified**:
- ✅ Non-blocking API (< 100ms response)
- ✅ Redis queue for background processing
- ✅ 4 notification channels (Email, SMS, WhatsApp, In-App)
- ✅ Windows-compatible worker
- ✅ Automatic retry with exponential backoff
- ✅ Per-channel status tracking
- ✅ Mock mode for testing without credentials
- ✅ Horizontally scalable (multiple workers)

