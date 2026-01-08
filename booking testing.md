# 🧪 Booking System Testing Guide

## ✅ What's Implemented

**Complete booking workflow with payment and vendor approval:**
- ✅ User creates booking
- ✅ User pays (mock Razorpay integration)
- ✅ Booking goes to vendor for approval
- ✅ Vendor approves → Booking confirmed
- ✅ Vendor rejects → Automatic refund

---

## 🚀 Step-by-Step Testing

### Prerequisites:
1. Server running at http://localhost:8000
2. Have a user account (or create one)
3. Have a vendor with service type mode: "booking"
4. Have a service configured with pricing

---

## 📋 PART 1: Setup (Detailed Step-by-Step)

### Step 1: Admin Login

**Endpoint**: `POST /admin/auth/login`

**Request Body**:
```json
{
  "email": "admin@doffair.com",
  "password": "admin123"
}
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Action**: 
1. Copy the `access_token`
2. Click the **Authorize** button in Swagger UI (top right)
3. Paste the token in the "Value" field
4. Click "Authorize" then "Close"

---

### Step 2: Create BOOKING Service Type

**Endpoint**: `POST /admin/service-types`

**Request Body**:
```json
{
  "code": "grooming",
  "display_name": "Pet Grooming",
  "description": "Professional pet grooming services",
  "mode": "booking"
}
```

⚠️ **IMPORTANT**: Use lowercase `"booking"` NOT `"BOOKING"`

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "679a1b2c3d4e5f6a7b8c9d0e",
    "code": "grooming",
    "display_name": "Pet Grooming",
    "description": "Professional pet grooming services",
    "mode": "booking",
    "is_active": true,
    "images": []
  }
}
```

**Action**: Copy the `id` value → This is your `service_type_id`

---

### Step 3: Vendor Login

**Endpoint**: `POST /vendor/auth/login`

**Request Body**:
```json
{
  "email": "vendor@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "vendor_id": "679b1c2d3e4f5a6b7c8d9e0f",
  "status": "APPROVED",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Action**:
1. Copy the `vendor_id` → Save this!
2. Copy the `access_token`
3. Click **Authorize** button and replace admin token with vendor token
4. Paste vendor token and click "Authorize" then "Close"

---

### Step 4: Vendor Selects Service Type

**Endpoint**: `POST /vendor/service-types/select`

**Request Body**:
```json
{
  "service_type_ids": ["679a1b2c3d4e5f6a7b8c9d0e"]
}
```

Replace `679a1b2c3d4e5f6a7b8c9d0e` with the actual service_type_id from Step 2.

**Expected Response**:
```json
{
  "success": true,
  "message": "Service types selected successfully"
}
```

---

### Step 5: Add Vendor Location

**Endpoint**: `POST /vendor/locations`

**Request Body**:
```json
{
  "name": "Main Branch",
  "address_line_1": "123 Pet Street",
  "address_line_2": "Suite 100",
  "city": "Hyderabad",
  "state": "Telangana",
  "pincode": "500084",
  "country": "India",
  "latitude": 17.385044,
  "longitude": 78.486671
}
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "679c1d2e3f4a5b6c7d8e9f0a",
    "name": "Main Branch",
    "address_line_1": "123 Pet Street",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500084"
  }
}
```

**Action**: Copy the `id` value → This is your `location_id`

---

### Step 6: Create a Service

**Endpoint**: `POST /vendor/services/base`

**Request Body**:
```json
{
  "location_id": "679c1d2e3f4a5b6c7d8e9f0a",
  "service_type_id": "679a1b2c3d4e5f6a7b8c9d0e",
  "name": "Basic Pet Grooming",
  "description": "Complete grooming package for your pet",
  "duration_minutes": 60,
  "delivery_mode": "BOTH"
}
```

Replace the IDs with your actual `location_id` and `service_type_id`.

**delivery_mode options**:
- `"CENTER"` - Only at vendor location
- `"HOME"` - Only at customer's home
- `"BOTH"` - Both options available

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "679d1e2f3a4b5c6d7e8f9a0b",
    "name": "Basic Pet Grooming",
    "description": "Complete grooming package for your pet",
    "duration_minutes": 60,
    "delivery_mode": "BOTH",
    "is_active": true
  }
}
```

**Action**: Copy the `id` value → This is your `service_id`

---

### Step 7: Configure Pricing for the Service

**Endpoint**: `POST /vendor/pricing`

**Request Body**:
```json
{
  "service_id": "679d1e2f3a4b5c6d7e8f9a0b",
  "location_id": "679c1d2e3f4a5b6c7d8e9f0a",
  "base_price": 500,
  "discount_type": "FLAT",
  "discount_value": 50
}
```

Replace `service_id` and `location_id` with your actual IDs.

**discount_type options**:
- `"NONE"` - No discount (set discount_value to 0)
- `"FLAT"` - Fixed amount off (e.g., ₹50 off)
- `"PERCENT"` - Percentage off (e.g., 10% off)

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "679e1f2a3b4c5d6e7f8a9b0c",
    "service_id": "679d1e2f3a4b5c6d7e8f9a0b",
    "base_price": 500,
    "discount_type": "FLAT",
    "discount_value": 50,
    "final_price": 450
  }
}
```

**✅ Vendor setup complete!** Final price will be ₹450 (₹500 - ₹50 discount)

---

### Step 8: User Signup (If No Account)

**Endpoint**: `POST /user/auth/signup`

**Request Body**:
```json
{
  "name": "John Doe",
  "phone": "9876543210",
  "email": "john@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "user_id": "679f1a2b3c4d5e6f7a8b9c0d",
  "name": "John Doe",
  "email": "john@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Step 9: User Login

**Endpoint**: `POST /user/auth/login`

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "user_id": "679f1a2b3c4d5e6f7a8b9c0d",
  "name": "John Doe",
  "email": "john@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Action**:
1. Copy the `user_id` → Save this!
2. Copy the `access_token`
3. Click **Authorize** button and replace vendor token with user token
4. Paste user token and click "Authorize" then "Close"

**✅ Setup Complete!** You now have:
- ✅ Service type created (booking mode)
- ✅ Vendor configured with location, service, and pricing
- ✅ User account ready

**Summary of IDs you should have**:
- `service_type_id`: 679a1b2c3d4e5f6a7b8c9d0e
- `vendor_id`: 679b1c2d3e4f5a6b7c8d9e0f
- `location_id`: 679c1d2e3f4a5b6c7d8e9f0a
- `service_id`: 679d1e2f3a4b5c6d7e8f9a0b
- `user_id`: 679f1a2b3c4d5e6f7a8b9c0d

---

## 📋 PART 2: Booking Flow (User Side)

### Step 10: Create Booking

**Endpoint**: `POST /bookings/create`

**Sample Data** (CENTER delivery):
```json
{
  "service_id": "679...",
  "booking_date": "2026-01-10T14:00:00",
  "delivery_mode": "CENTER"
}
```

**Sample Data** (HOME delivery):
```json
{
  "service_id": "679...",
  "booking_date": "2026-01-10T14:00:00",
  "delivery_mode": "HOME",
  "service_address": "123 Main Street, Apt 4B",
  "service_city": "Hyderabad",
  "service_pincode": "500084"
}
```

**Expected Response**:
```json
{
  "booking_id": "679abc...",
  "service_name": "Basic Grooming",
  "vendor_name": "Pawsome Pet Care",
  "booking_date": "2026-01-10T14:00:00",
  "final_amount": 500.0,
  "status": "PENDING_PAYMENT",
  "payment_required": true,
  "message": "Booking created successfully. Please proceed with payment."
}
```

**Copy the `booking_id`!**

---

### Step 11: Initiate Payment

**Endpoint**: `POST /bookings/initiate-payment`

```json
{
  "booking_id": "679abc...",
  "payment_method": "razorpay"
}
```

**Expected Response**:
```json
{
  "payment_id": "679xyz...",
  "booking_id": "679abc...",
  "amount": 500.0,
  "currency": "INR",
  "payment_gateway_order_id": "order_1a2b3c4d5e6f",
  "message": "Payment initiated. Please complete payment on Razorpay."
}
```

**Copy**:
- `payment_id`
- `payment_gateway_order_id`

---

### Step 12: Confirm Payment (Simulate Razorpay Success)

**Endpoint**: `POST /bookings/confirm-payment`

```json
{
  "booking_id": "679abc...",
  "payment_id": "679xyz...",
  "payment_gateway_payment_id": "pay_mock123",
  "payment_gateway_signature": "signature_mock456"
}
```

**Expected Response**:
```json
{
  "booking_id": "679abc...",
  "payment_id": "679xyz...",
  "status": "PENDING_APPROVAL",
  "message": "Payment confirmed! Your booking is now pending vendor approval."
}
```

**✅ Success! Booking is now waiting for vendor approval!**

---

### Step 13: View My Bookings (User)

**Endpoint**: `GET /bookings/my-bookings`

**Expected**: You'll see your booking with status `PENDING_APPROVAL`

---

## 📋 PART 3: Vendor Approval

### Step 14: Switch to Vendor Token

**Authorize with VENDOR token** (from Step 3)

---

### Step 15: View Pending Approvals

**Endpoint**: `GET /bookings/vendor/pending-approvals`

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "booking_id": "679abc...",
      "user_name": "John Doe",
      "user_phone": "9876543210",
      "user_email": "user@example.com",
      "service_name": "Basic Grooming",
      "booking_date": "2026-01-10T14:00:00",
      "delivery_mode": "CENTER",
      "final_amount": 500.0,
      "status": "PENDING_APPROVAL",
      "payment_status": "SUCCESS"
    }
  ]
}
```

**✅ Vendor can see the booking request!**

---

### Step 16A: APPROVE Booking

**Endpoint**: `POST /bookings/vendor/{booking_id}/approve`

```json
{
  "notes": "Confirmed! Please arrive 10 minutes early."
}
```

**Expected Response**:
```json
{
  "booking_id": "679abc...",
  "status": "CONFIRMED",
  "message": "Booking approved successfully! Service scheduled for 2026-01-10 14:00",
  "refund_initiated": false
}
```

**✅ Booking confirmed! Service scheduled!**

---

### Step 16B: REJECT Booking (Alternative)

**Endpoint**: `POST /bookings/vendor/{booking_id}/reject`

```json
{
  "rejection_reason": "Fully booked for that time slot. Please choose another time."
}
```

**Expected Response**:
```json
{
  "booking_id": "679abc...",
  "status": "REJECTED",
  "message": "Booking rejected. Refund has been initiated.",
  "refund_initiated": true
}
```

**✅ Booking rejected! Refund automatically triggered!**

---

## 📋 PART 4: View All Bookings

### User View Bookings

**Endpoint**: `GET /bookings/my-bookings`

Shows all user's bookings with status:
- `PENDING_PAYMENT` - Not paid yet
- `PENDING_APPROVAL` - Paid, waiting for vendor
- `CONFIRMED` - Approved by vendor
- `REJECTED` - Rejected by vendor (refunded)

---

### Vendor View All Bookings

**Endpoint**: `GET /bookings/vendor/my-bookings`

**With filter**:
`GET /bookings/vendor/my-bookings?status=CONFIRMED`

Shows all vendor's bookings, can filter by status.

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path (Approval)
```
User creates booking
  → Pays
  → Vendor approves
  → Status: CONFIRMED ✅
```

### Scenario 2: Rejection & Refund
```
User creates booking
  → Pays
  → Vendor rejects
  → Status: REJECTED
  → Payment status: REFUNDED ✅
```

### Scenario 3: Multiple Bookings
- Create 3 bookings
- Approve 1
- Reject 1
- Leave 1 pending
- Check all views work correctly

---

## 📊 Status Flow Diagram

```
User creates booking
    ↓
PENDING_PAYMENT
    ↓ (user pays)
PENDING_APPROVAL
    ↓
[Vendor Decision]
    ↓                     ↓
CONFIRMED            REJECTED
(Service scheduled)  (Refund issued)
```

---

## 🎯 Key Features to Test

### ✅ Validation Tests:
1. Try booking without login → 401 error
2. Try booking non-existent service → 404 error
3. Try booking LEAD mode service → Error (only booking mode)
4. Try HOME delivery without address → 400 error
5. Try approving with wrong vendor → 403 error
6. Try approving already confirmed booking → 400 error

### ✅ Business Logic Tests:
1. Final amount calculation (base price - discount)
2. Payment status tracking
3. Refund on rejection
4. Vendor can only see their bookings
5. User can only see their bookings

---
