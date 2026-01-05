# 🧪 Lead Generation Testing Guide

## ✅ Implementation Complete!

The lead generation feature is now fully implemented with:
- ✅ User signup and authentication
- ✅ Reveal vendor mobile (with daily limit of 5)
- ✅ Lead tracking for vendors
- ✅ Mark lead as contacted (vendor action)
- ✅ Duplicate prevention
- ✅ Service type mode validation (only LEAD mode services)

---

## 🚀 Step-by-Step Testing Instructions

### Prerequisites:
1. Server is running at http://localhost:8000
2. Open http://localhost:8000/docs in your browser
3. Have a vendor account ready (or create one)
4. Have a service type with `mode: LEAD` (we'll create this)

---

## 📋 PART 1: Setup (Admin Actions)

### Step 1: Admin Login

**Endpoint**: `POST /admin/auth/login`

**Sample Data**:
```json
{
  "email": "admin@doffair.com",
  "password": "admin123"
}
```

**Expected Response**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Action**: Copy the `access_token` and click **Authorize** button, paste it.

---

### Step 2: Create LEAD Service Type (Admin)

**Endpoint**: `POST /admin/service-types`

**Sample Data**:
```json
{
  "code": "vet_consultation",
  "display_name": "Veterinary Consultation",
  "description": "Expert veterinary consultation for your pets",
  "mode": "lead"
}
```

⚠️ **IMPORTANT**: Use lowercase `"lead"` NOT uppercase `"LEAD"`

**Expected Response**:
```json
{
  "data": {
    "id": "67...abc",
    "code": "vet_consultation",
    "display_name": "Veterinary Consultation",
    "mode": "LEAD",
    "is_active": true
  }
}
```

**Action**: Copy the `id` value (this is your `service_type_id`)

---

## 📋 PART 2: Vendor Setup

### Step 3: Vendor Login (or Signup if new)

**Endpoint**: `POST /vendor/auth/login`

**Sample Data**:
```json
{
  "email": "vendor@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "vendor_id": "67...xyz",
  "status": "SERVICES_CONFIGURED",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Actions**:
1. Copy the `vendor_id`
2. Copy the `access_token`
3. Click **Authorize** button and paste the vendor token

---

### Step 4: Vendor Selects LEAD Service Type

**Endpoint**: `POST /vendor/onboarding/{vendor_id}/service-types`

**Sample Data** (replace {vendor_id} in URL):
```json
{
  "service_type_ids": [
    "67...abc"
  ]
}
```
(Use the service_type_id from Step 2)

**Expected Response**:
```json
{
  "message": "Service types selected successfully",
  "data": {
    "vendor_id": "67...xyz",
    "status": "SERVICE_TYPE_SELECTED"
  }
}
```

---

## 📋 PART 3: User Setup

### Step 5: Create User Account

**Endpoint**: `POST /user/auth/signup`

**Sample Data**:
```json
{
  "name": "Rahul Kumar",
  "phone": "9876543210",
  "email": "rahul@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "User account created successfully",
  "data": {
    "user_id": "67...user1",
    "name": "Rahul Kumar",
    "email": "rahul@example.com"
  }
}
```

---

### Step 6: User Login

**Endpoint**: `POST /user/auth/login`

**Sample Data**:
```json
{
  "email": "rahul@example.com",
  "password": "password123"
}
```

**Expected Response**:
```json
{
  "user_id": "67...user1",
  "name": "Rahul Kumar",
  "email": "rahul@example.com",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Action**: 
1. Copy the `user_id`
2. Copy the `access_token`
3. Click **Authorize** button and paste the USER token (replace vendor token)

---

## 📋 PART 4: Lead Generation (The Main Feature!)

### Step 7: Check Daily Limit (Optional)

**Endpoint**: `GET /leads/my-daily-limit`

**No request body needed**

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "current_count": 0,
    "daily_limit": 5,
    "remaining": 5,
    "can_reveal_more": true
  }
}
```

---

### Step 8: 🔥 Reveal Vendor Mobile (CREATE LEAD!)

**Endpoint**: `POST /leads/reveal-mobile`

**Sample Data**:
```json
{
  "vendor_id": "67...xyz",
  "service_type_id": "67...abc"
}
```
(Use vendor_id from Step 3 and service_type_id from Step 2)

**Expected Response**:
```json
{
  "lead_id": "67...lead1",
  "vendor_name": "Pawsome Pet Care",
  "vendor_phone": "+919123456789",
  "vendor_email": "vendor@example.com",
  "service_type_name": "Veterinary Consultation",
  "message": "Contact revealed successfully! You can now reach out to Pawsome Pet Care."
}
```

**✅ SUCCESS! The lead is created and user can see vendor's contact!**

---

### Step 9: Test Daily Limit

**Action**: Repeat Step 8 with the same data 5 MORE times.

**After 5th reveal, Expected Response**:
```json
{
  "detail": "Daily limit reached. You have already revealed 5 contacts today. Maximum is 5 per day."
}
```
**Status Code**: 429 (Too Many Requests)

**✅ Daily limit is working!**

---

### Step 10: Test Duplicate Prevention

**Action**: Try Step 8 again tomorrow (or change system date for testing)

**Expected**: Should return the existing lead, not create a new one.

---

### Step 11: View My Leads (User)

**Endpoint**: `GET /leads/my-leads`

**No request body needed**

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "lead_id": "67...lead1",
      "user_name": "Rahul Kumar",
      "user_phone": "9876543210",
      "user_email": "rahul@example.com",
      "service_type_name": "Veterinary Consultation",
      "revealed_at": "2026-01-05T12:30:00Z",
      "is_contacted": false,
      "contacted_at": null,
      "notes": null
    }
  ]
}
```

---

## 📋 PART 5: Vendor Dashboard

### Step 12: Switch to Vendor Token

**Action**:
1. Click **Authorize** button
2. Paste the VENDOR token from Step 3
3. Click **Authorize**

---

### Step 13: View Vendor Leads

**Endpoint**: `GET /leads/vendor/my-leads`

**No request body needed**

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "lead_id": "67...lead1",
      "user_name": "Rahul Kumar",
      "user_phone": "9876543210",
      "user_email": "rahul@example.com",
      "service_type_name": "Veterinary Consultation",
      "revealed_at": "2026-01-05T12:30:00Z",
      "is_contacted": false,
      "contacted_at": null,
      "notes": null
    }
  ]
}
```

**✅ Vendor can see who revealed their contact!**

---

### Step 14: Mark Lead as Contacted

**Endpoint**: `PATCH /leads/vendor/{lead_id}/mark-contacted`

**Sample Data**:
```json
{
  "notes": "Called the customer. Scheduled appointment for tomorrow."
}
```
(Replace {lead_id} in URL with the lead_id from Step 13)

**Expected Response**:
```json
{
  "success": true,
  "message": "Lead marked as contacted",
  "data": {
    "lead_id": "67...lead1",
    "is_contacted": true,
    "contacted_at": "2026-01-05T12:45:00Z",
    "notes": "Called the customer. Scheduled appointment for tomorrow."
  }
}
```

**✅ Lead tracking is working!**

---

## 🧪 Additional Test Cases

### Test Case 1: Try to reveal BOOKING service (Should Fail)

**Action**: Create a service type with `mode: BOOKING` and try to reveal it

**Expected**: Error message "This service type is in BOOKING mode, not LEAD mode"

---

### Test Case 2: Create Multiple Users

Create 2-3 more users and test:
- Each user has their own daily limit (5 per day)
- Users can reveal the same vendor (multiple leads for one vendor)
- Users can reveal different vendors

---

### Test Case 3: Vendor with Multiple Service Types

**Action**:
1. Create 2 service types with mode: LEAD
2. Vendor selects both
3. User reveals contact for both service types
4. Vendor should see 2 separate leads

---

## 📊 Summary of What Was Tested

✅ **User Management**:
- User signup
- User login
- User authentication

✅ **Lead Generation**:
- Reveal vendor mobile
- Daily limit (5 per day)
- Duplicate prevention
- View user's leads

✅ **Vendor Dashboard**:
- View all leads
- Mark lead as contacted
- Add notes to leads

✅ **Validation**:
- Only LEAD mode services can be revealed
- Vendor must be active
- Service type must exist


Implementation Summary:
- Created User module (signup, login, authentication)
- Created Lead model with daily limit tracking
- Implemented reveal mobile endpoint with 5/day limit
- Added duplicate lead prevention
- Created vendor dashboard to view/manage leads
- Added lead status tracking (contacted/not contacted)

Test Results:
✅ User can signup and login
✅ User can reveal vendor contact (creates lead)
✅ Daily limit of 5 enforced correctly
✅ Duplicate leads prevented
✅ Vendor can view all their leads
✅ Vendor can mark leads as contacted
✅ Only LEAD mode services can be revealed
✅ All validations working properly

Database Collections Added:
- users (customer accounts)
- leads (contact reveals tracking)

API Endpoints Added:
- POST /user/auth/signup
- POST /user/auth/login
- GET /leads/my-daily-limit
- POST /leads/reveal-mobile
- GET /leads/my-leads
- GET /leads/vendor/my-leads
- PATCH /leads/vendor/{lead_id}/mark-contacted

