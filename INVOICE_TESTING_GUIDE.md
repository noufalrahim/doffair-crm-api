# 📄 Invoice System - Complete Testing Guide

## 🎯 Overview

The Invoice System provides **complete invoice lifecycle management** with:
- ✅ Auto-generation from completed bookings
- ✅ Configurable tax rules (GST, CGST+SGST, IGST, VAT)
- ✅ Full CRUD operations with validation
- ✅ Automatic customer notifications
- ✅ Complete audit trail for compliance
- ✅ Payment tracking (full/partial)
- ✅ Role-based access control

---

## 📚 Table of Contents

1. [Tax Configuration](#tax-configuration)
2. [Invoice Generation](#invoice-generation)
3. [Invoice Management](#invoice-management)
4. [Payment Recording](#payment-recording)
5. [Audit Trail](#audit-trail)
6. [Testing Scenarios](#testing-scenarios)
7. [API Reference](#api-reference)

---

## 🔧 Part 1: Tax Configuration

### Step 1: Create Tax Configuration

**Endpoint**: `POST /vendor/invoices/tax-config`

**Sample Request** (GST 18%):
```json
{
  "location_id": null,
  "tax_type": "GST",
  "tax_name": "GST 18%",
  "tax_percentage": 18.0,
  "cgst_percentage": 0.0,
  "sgst_percentage": 0.0,
  "service_charge_percentage": 0.0,
  "other_charges": {},
  "is_default": true,
  "notes": "Standard GST for all services"
}
```

**Sample Request** (CGST + SGST for intra-state):
```json
{
  "location_id": "location123",
  "tax_type": "CGST_SGST",
  "tax_name": "CGST 9% + SGST 9%",
  "tax_percentage": 18.0,
  "cgst_percentage": 9.0,
  "sgst_percentage": 9.0,
  "service_charge_percentage": 2.0,
  "other_charges": {
    "handling_fee": 50.0
  },
  "is_default": false,
  "notes": "For Hyderabad location"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Tax configuration created successfully",
  "data": {
    "id": "tax_config_id",
    "vendor_id": "vendor_id",
    "tax_type": "GST",
    "tax_name": "GST 18%",
    "tax_percentage": 18.0,
    "is_default": true
  }
}
```

**Copy the `tax_config_id`!**

---

### Step 2: View All Tax Configurations

**Endpoint**: `GET /vendor/invoices/tax-config`

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "tax_config_id",
      "tax_name": "GST 18%",
      "tax_percentage": 18.0,
      "is_default": true,
      "is_active": true
    }
  ]
}
```

---

## 📄 Part 2: Invoice Generation

### Prerequisites
1. Booking must be in **COMPLETED** status
2. No existing invoice for this booking
3. Tax configuration must be set up

### Step 3: Complete a Booking First

Follow `booking testing.md` to create and complete a booking.

**Mark booking as completed** (this is typically done by vendor after service):
```
POST /bookings/vendor/{booking_id}/complete
```

---

### Step 4: Generate Invoice from Booking

**Endpoint**: `POST /vendor/invoices/generate`

**Sample Request**:
```json
{
  "booking_id": "679abc123...",
  "due_days": 30,
  "notes": "Thank you for choosing our services",
  "terms_and_conditions": "Payment due within 30 days. Late fees apply after due date.",
  "auto_send": true
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Invoice generated successfully: INV-2026-V12345-0001",
  "data": {
    "id": "invoice_id",
    "invoice_number": "INV-2026-V12345-0001",
    "customer_name": "John Doe",
    "service_name": "Basic Grooming",
    "invoice_date": "2026-02-05T12:00:00",
    "due_date": "2026-03-07T12:00:00",
    "subtotal": 500.0,
    "discount_amount": 50.0,
    "tax_amount": 81.0,
    "grand_total": 531.0,
    "balance_due": 531.0,
    "status": "SENT",
    "sent_count": 1
  }
}
```

**Copy the `invoice_id` and `invoice_number`!**

---

## 📊 Part 3: Invoice Management

### Step 5: View All Invoices

**Endpoint**: `GET /vendor/invoices/`

**Query Parameters**:
- `status` - Filter by status (DRAFT, GENERATED, SENT, PAID, etc.)
- `customer_id` - Filter by customer
- `limit` - Number of results (default 50, max 100)
- `skip` - Pagination offset

**Example**:
```
GET /vendor/invoices/?status=SENT&limit=20
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "invoice_id",
      "invoice_number": "INV-2026-V12345-0001",
      "invoice_date": "2026-02-05T12:00:00",
      "customer_name": "John Doe",
      "service_name": "Basic Grooming",
      "grand_total": 531.0,
      "balance_due": 531.0,
      "status": "SENT",
      "sent_count": 1
    }
  ]
}
```

---

### Step 6: Get Invoice Details

**Endpoint**: `GET /vendor/invoices/{invoice_id}`

**Expected Response**: Complete invoice with all details including tax breakdown

---

### Step 7: Update Invoice (DRAFT only)

**Endpoint**: `PATCH /vendor/invoices/{invoice_id}`

**Note**: Only DRAFT invoices can be edited!

**Sample Request**:
```json
{
  "discount_amount": 100.0,
  "due_date": "2026-03-15T12:00:00",
  "notes": "Updated discount applied"
}
```

---

### Step 8: Resend Invoice

**Endpoint**: `POST /vendor/invoices/{invoice_id}/send`

**Sample Request**:
```json
{
  "channels": ["email", "sms", "whatsapp"],
  "notes": "Resending invoice as per customer request"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Invoice INV-2026-V12345-0001 sent successfully via email, sms, whatsapp",
  "data": {
    "invoice_id": "invoice_id",
    "sent_count": 2
  }
}
```

---

## 💰 Part 4: Payment Recording

### Step 9: Mark Invoice as Paid (Full Payment)

**Endpoint**: `POST /vendor/invoices/{invoice_id}/mark-paid`

**Sample Request** (Full Payment):
```json
{
  "paid_amount": 531.0,
  "payment_method": "UPI",
  "payment_reference": "UPI123456789",
  "payment_date": "2026-02-06T10:30:00",
  "notes": "Payment received via UPI"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Payment recorded: ₹531.0. Status: PAID",
  "data": {
    "invoice_id": "invoice_id",
    "invoice_number": "INV-2026-V12345-0001",
    "paid_amount": 531.0,
    "balance_due": 0.0,
    "status": "PAID"
  }
}
```

---

### Step 10: Mark Invoice as Paid (Partial Payment)

**Sample Request** (Partial Payment):
```json
{
  "paid_amount": 300.0,
  "payment_method": "CASH",
  "payment_reference": null,
  "notes": "Partial payment received"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Payment recorded: ₹300.0. Status: PARTIALLY_PAID",
  "data": {
    "paid_amount": 300.0,
    "balance_due": 231.0,
    "status": "PARTIALLY_PAID"
  }
}
```

---

## 🗑️ Part 5: Cancel Invoice

### Step 11: Cancel Invoice

**Endpoint**: `POST /vendor/invoices/{invoice_id}/cancel`

**Sample Request**:
```json
{
  "reason": "Customer requested cancellation due to service issue. Full refund issued."
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Invoice INV-2026-V12345-0001 cancelled successfully",
  "data": {
    "invoice_id": "invoice_id",
    "status": "CANCELLED"
  }
}
```

**Note**: Cannot cancel PAID, REFUNDED, or already CANCELLED invoices!

---

## 📜 Part 6: Audit Trail

### Step 12: View Complete Audit Log

**Endpoint**: `GET /vendor/invoices/{invoice_id}/audit-logs`

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "log_id_1",
      "invoice_number": "INV-2026-V12345-0001",
      "action": "GENERATED",
      "performed_by": "vendor_id",
      "performed_by_role": "vendor",
      "notes": "Auto-generated from booking 679abc123",
      "timestamp": "2026-02-05T12:00:00"
    },
    {
      "id": "log_id_2",
      "action": "SENT",
      "performed_by": "vendor_id",
      "notes": "Sent via email",
      "timestamp": "2026-02-05T12:00:05"
    },
    {
      "id": "log_id_3",
      "action": "PAYMENT_RECEIVED",
      "performed_by": "vendor_id",
      "notes": "Payment received: ₹531.0 via UPI. Reference: UPI123456789",
      "timestamp": "2026-02-06T10:30:00"
    }
  ]
}
```

---

## 🧪 Part 7: Testing Scenarios

### Scenario 1: Complete Invoice Lifecycle
```
1. Create tax configuration (GST 18%)
2. Complete a booking
3. Generate invoice from booking → auto-sent to customer
4. Customer receives email/SMS/WhatsApp notification
5. Mark invoice as paid
6. View audit log → all actions recorded ✅
```

---

### Scenario 2: Partial Payments
```
1. Generate invoice: ₹1000
2. Receive partial payment: ₹500 → Status: PARTIALLY_PAID
3. Receive remaining: ₹500 → Status: PAID ✅
```

---

### Scenario 3: Invoice Cancellation
```
1. Generate invoice
2. Send to customer
3. Customer disputes service
4. Cancel invoice with reason → audit log updated ✅
```

---

### Scenario 4: Multiple Tax Configurations
```
1. Create default GST 18% (vendor-wide)
2. Create location-specific CGST+SGST for Hyderabad
3. Create IGST for inter-state customers
4. Generate invoices → correct tax applied based on location ✅
```

---

### Scenario 5: Resending Invoices
```
1. Generate and send invoice → sent_count = 1
2. Customer says didn't receive
3. Resend invoice → sent_count = 2
4. View audit log → both SENT actions logged ✅
```

---

## 🔍 Part 8: Validation Tests

### ✅ Test Invalid Operations:

1. **Generate invoice for incomplete booking** → Error
2. **Generate invoice for already invoiced booking** → Error
3. **Edit SENT invoice** → Error (only DRAFT can be edited)
4. **Cancel PAID invoice** → Error
5. **Send CANCELLED invoice** → Error
6. **Mark negative amount as paid** → Error
7. **Access another vendor's invoice** → 403 Access Denied

---

## 📋 Part 9: API Reference

### Invoice Status Flow

```
DRAFT → GENERATED → SENT → PAID
                       ↓
                  PARTIALLY_PAID → PAID
                       ↓
                  OVERDUE
                       ↓
                  CANCELLED
```

---

### Tax Types

| Tax Type | Description | Example |
|----------|-------------|---------|
| NONE | No tax | - |
| GST | Combined GST | 18% GST |
| CGST_SGST | Split tax (intra-state) | 9% CGST + 9% SGST |
| IGST | Integrated GST (inter-state) | 18% IGST |
| VAT | Value Added Tax | 12% VAT |
| CUSTOM | Custom configuration | Any custom tax |

---

### Payment Methods

- CASH
- UPI
- CARD
- BANK_TRANSFER
- CHEQUE
- ONLINE
- OTHER

---

### Audit Actions

- **CREATED** - Invoice manually created
- **GENERATED** - Auto-generated from booking
- **EDITED** - Invoice details changed
- **SENT** - Sent to customer (first time)
- **RESENT** - Resent to customer
- **PAYMENT_RECEIVED** - Payment recorded
- **CANCELLED** - Invoice cancelled
- **REFUNDED** - Refund issued

---

## 🎯 Key Features

### 1. Auto-Generation
- ✅ Automatically generates from completed bookings
- ✅ Fetches customer and vendor details
- ✅ Applies default tax configuration
- ✅ Generates unique invoice number
- ✅ Creates audit log entry

### 2. Tax Configuration
- ✅ Multiple tax configs per vendor
- ✅ Location-specific configurations
- ✅ Default configuration support
- ✅ GST, CGST+SGST, IGST, VAT support

### 3. Audit Trail
- ✅ Every action is logged
- ✅ Field-level change tracking
- ✅ Performer and timestamp recorded
- ✅ Immutable audit records
- ✅ Complete compliance support

### 4. Notifications
- ✅ Auto-send on generation
- ✅ Multi-channel support (email, SMS, WhatsApp)
- ✅ Resend capability
- ✅ Template-based notifications

### 5. Payment Tracking
- ✅ Full payment support
- ✅ Partial payment support
- ✅ Payment method recording
- ✅ Transaction reference tracking

### 6. Security
- ✅ Role-based access control
- ✅ Vendor can only access own invoices
- ✅ Validation at every step
- ✅ Status-based operation restrictions

---

## 🚀 Quick Start

```bash
# 1. Set up tax config
POST /vendor/invoices/tax-config
{
  "tax_type": "GST",
  "tax_name": "GST 18%",
  "tax_percentage": 18.0,
  "is_default": true
}

# 2. Complete a booking
POST /bookings/vendor/{booking_id}/complete

# 3. Generate invoice
POST /vendor/invoices/generate
{
  "booking_id": "booking_id",
  "due_days": 30,
  "auto_send": true
}

# 4. Mark as paid
POST /vendor/invoices/{invoice_id}/mark-paid
{
  "paid_amount": 531.0,
  "payment_method": "UPI"
}

# 5. View audit log
GET /vendor/invoices/{invoice_id}/audit-logs
```

---

## ⚠️ Important Notes

1. **Booking Status**: Only COMPLETED bookings can be invoiced
2. **One Invoice Per Booking**: Cannot generate duplicate invoices
3. **Edit Restrictions**: Only DRAFT invoices can be edited
4. **Cancel Restrictions**: Cannot cancel PAID/REFUNDED invoices
5. **Audit Trail**: All actions are permanently logged
6. **Tax Configuration**: Set up before generating invoices
7. **Notifications**: Email notifications sent automatically

---

## 📞 Support

If you encounter any issues:
1. Check audit logs for action history
2. Verify booking is COMPLETED
3. Ensure tax configuration is set up
4. Check invoice status allows the operation

---

**Modular Design**: Invoice system follows the same pattern as Booking, Prescription, and Reminder systems for consistency and maintainability.
