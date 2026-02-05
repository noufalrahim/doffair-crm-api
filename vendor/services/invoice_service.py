"""
Comprehensive Invoice Service
Auto-generation from bookings, CRUD operations, audit trail
"""
from datetime import datetime, timedelta
from typing import Optional, List
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from vendor.models.invoice import Invoice, InvoiceLineItem, InvoiceTaxConfig, InvoiceAuditLog
from vendor.models.vendor import Vendor
from user.models.booking import Booking
from vendor.utils.invoice_utils import (
    generate_invoice_number,
    calculate_line_item_totals,
    calculate_invoice_totals,
    calculate_balance_due,
    validate_invoice_edit_allowed,
    validate_invoice_send_allowed,
    validate_invoice_cancel_allowed
)
from core.enums import InvoiceStatus, InvoiceAuditAction, BookingStatus
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource

logger = logging.getLogger(__name__)


# ============================================
# Audit Logging
# ============================================

async def create_audit_log(
    engine: AIOEngine,
    invoice_id: str,
    invoice_number: str,
    action: InvoiceAuditAction,
    performed_by: str,
    performed_by_role: str = "vendor",
    field_changed: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None
):
    """Create audit log entry for invoice action"""
    audit_log = InvoiceAuditLog(
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        action=action.value if hasattr(action, 'value') else action,
        performed_by=performed_by,
        performed_by_role=performed_by_role,
        field_changed=field_changed,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        reason=reason,
        notes=notes
    )
    await engine.save(audit_log)
    logger.info(f"📝 Audit log created: {action} for invoice {invoice_number} by {performed_by}")


# ============================================
# Tax Configuration
# ============================================

async def create_tax_config(
    engine: AIOEngine,
    vendor_id: str,
    payload
) -> InvoiceTaxConfig:
    """Create tax configuration for vendor"""
    
    # If setting as default, unset other defaults
    if payload.is_default:
        existing_defaults = await engine.find(
            InvoiceTaxConfig,
            (InvoiceTaxConfig.vendor_id == vendor_id) & (InvoiceTaxConfig.is_default == True)
        )
        for config in existing_defaults:
            config.is_default = False
            await engine.save(config)
    
    tax_config = InvoiceTaxConfig(
        vendor_id=vendor_id,
        location_id=payload.location_id,
        tax_type=payload.tax_type,
        tax_name=payload.tax_name,
        tax_percentage=payload.tax_percentage,
        cgst_percentage=payload.cgst_percentage,
        sgst_percentage=payload.sgst_percentage,
        service_charge_percentage=payload.service_charge_percentage,
        other_charges=payload.other_charges,
        is_default=payload.is_default,
        notes=payload.notes
    )
    
    await engine.save(tax_config)
    logger.info(f"✅ Tax config created for vendor {vendor_id}: {tax_config.tax_name}")
    return tax_config


async def get_default_tax_config(
    engine: AIOEngine,
    vendor_id: str,
    location_id: Optional[str] = None
) -> Optional[InvoiceTaxConfig]:
    """Get default tax config for vendor/location"""
    
    # Try location-specific first
    if location_id:
        config = await engine.find_one(
            InvoiceTaxConfig,
            (InvoiceTaxConfig.vendor_id == vendor_id) &
            (InvoiceTaxConfig.location_id == location_id) &
            (InvoiceTaxConfig.is_default == True) &
            (InvoiceTaxConfig.is_active == True)
        )
        if config:
            return config
    
    # Fall back to vendor-wide default
    config = await engine.find_one(
        InvoiceTaxConfig,
        (InvoiceTaxConfig.vendor_id == vendor_id) &
        (InvoiceTaxConfig.location_id == None) &
        (InvoiceTaxConfig.is_default == True) &
        (InvoiceTaxConfig.is_active == True)
    )
    return config


# ============================================
# Invoice Generation from Booking
# ============================================

async def generate_invoice_from_booking(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str,
    due_days: int = 30,
    notes: Optional[str] = None,
    terms_and_conditions: Optional[str] = None,
    auto_send: bool = True
) -> Invoice:
    """
    Auto-generate invoice from completed booking
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        booking_id: Booking ID to generate invoice from
        due_days: Days until payment due
        notes: Optional invoice notes
        terms_and_conditions: Optional T&C
        auto_send: Automatically send to customer
    
    Returns:
        Generated Invoice
    
    Raises:
        HTTPException: If booking not found, already invoiced, or not completed
    """
    # Fetch booking
    try:
        booking = await engine.find_one(
            Booking,
            (Booking.id == ObjectId(booking_id)) & (Booking.vendor_id == vendor_id)
        )
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found or access denied"
            )
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid booking ID: {booking_id}"
        )
    
    # Check if booking is completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate invoice. Booking status is {booking.status}. Must be COMPLETED."
        )
    
    # Check if invoice already exists using direct MongoDB query
    existing_invoice = await engine.get_collection(Invoice).find_one({
        "booking_id": booking_id,
        "is_active": True
    })
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice already exists for this booking: {existing_invoice.get('invoice_number')}"
        )
    
    # Fetch vendor details
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Get tax configuration
    tax_config = await get_default_tax_config(engine, vendor_id, booking.location_id)
    
    # Generate invoice number
    current_year = datetime.utcnow().year
    # Count existing invoices for this vendor this year
    year_start = datetime(current_year, 1, 1)
    invoice_count = await engine.count(
        Invoice,
        (Invoice.vendor_id == vendor_id) & (Invoice.created_at >= year_start)
    )
    invoice_number = generate_invoice_number(vendor_id, current_year, invoice_count + 1)
    
    # Calculate totals
    subtotal = booking.final_amount
    
    # Calculate invoice totals with tax
    totals = calculate_invoice_totals(
        line_items_total=subtotal,
        discount_amount=booking.discount_amount,
        discount_percentage=0.0,
        tax_config=tax_config,
        service_charge_amount=0.0,
        other_charges={}
    )
    
    # Create invoice document directly in MongoDB to bypass ODMantic validation issues
    now = datetime.utcnow()
    due_date_value = now + timedelta(days=due_days)
    
    invoice_doc = {
        "vendor_id": vendor_id,
        "customer_id": booking.user_id,
        "booking_id": booking_id,
        
        "invoice_number": invoice_number,
        "invoice_date": now,
        "due_date": due_date_value,
        
        # Customer details
        "customer_name": booking.user_name,
        "customer_email": booking.user_email,
        "customer_phone": booking.user_phone,
        "customer_address": f"{booking.service_address or ''}, {booking.service_city or ''}, {booking.service_pincode or ''}".strip(', '),
        
        # Vendor details
        "vendor_name": vendor.legal_name or f"Vendor {vendor_id[:8]}",
        "vendor_email": vendor.primary_contact_email,
        "vendor_phone": vendor.primary_contact_phone,
        "vendor_address": None,
        "vendor_gstin": None,
        
        # Service details
        "service_name": booking.service_name,
        "service_date": booking.booking_date,
        
        # Financial details
        "subtotal": totals['subtotal'],
        "discount_amount": totals['discount_amount'],
        "discount_percentage": 0.0,
        
        # Tax breakdown
        "tax_type": totals['tax_type'].value,
        "tax_amount": totals['tax_amount'],
        "cgst_amount": totals['cgst_amount'],
        "sgst_amount": totals['sgst_amount'],
        "igst_amount": totals['igst_amount'],
        
        # Charges
        "service_charge": totals['service_charge'],
        "other_charges": totals['other_charges'],
        
        # Totals
        "total_before_tax": totals['total_before_tax'],
        "total_tax": totals['total_tax'],
        "grand_total": totals['grand_total'],
        
        # Payment
        "paid_amount": 0.0,
        "balance_due": totals['grand_total'],
        
        "status": InvoiceStatus.GENERATED.value,
        "sent_at": None,
        "sent_count": 0,
        "cancelled_at": None,
        "cancellation_reason": None,
        "cancelled_by": None,
        "payment_received_at": None,
        "payment_method": None,
        "payment_reference": None,
        
        "notes": notes,
        "terms_and_conditions": terms_and_conditions or "Payment due within 30 days. Thank you for your business!",
        
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Insert directly into MongoDB
    result = await engine.get_collection(Invoice).insert_one(invoice_doc)
    invoice_doc['_id'] = result.inserted_id
    
    # Map _id to id for model_construct
    invoice_doc['id'] = invoice_doc.pop('_id')
    
    # Use model_construct to create Invoice object without validation
    invoice = Invoice.model_construct(**invoice_doc)
    logger.info(f"📄 Invoice generated: {invoice_number} for booking {booking_id}")
    
    # Create audit log
    await create_audit_log(
        engine=engine,
        invoice_id=str(invoice.id),
        invoice_number=invoice_number,
        action=InvoiceAuditAction.GENERATED,
        performed_by=vendor_id,
        notes=f"Auto-generated from booking {booking_id}"
    )
    
    # Auto-send if requested
    if auto_send:
        await send_invoice(engine, vendor_id, str(invoice.id), channels=["email"])
    
    return invoice


# ============================================
# Send Invoice to Customer
# ============================================

async def send_invoice(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str,
    channels: List[str] = ["email"],
    notes: Optional[str] = None
) -> Invoice:
    """
    Send invoice to customer via notification channels
    
    Args:
        engine: Database engine
        vendor_id: Vendor ID
        invoice_id: Invoice ID
        channels: Notification channels (email, sms, whatsapp)
        notes: Optional notes
    
    Returns:
        Updated Invoice
    """
    # Fetch invoice using MongoDB to bypass validation
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Validate can send
    if not validate_invoice_send_allowed(invoice.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send invoice with status {invoice.status}"
        )
    
    # Publish notification event
    try:
        event_publisher.publish(
            event_type=EventType.CUSTOM,  # We'll add INVOICE_SENT to EventType
            data={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "customer_id": invoice.customer_id,
                "customer_name": invoice.customer_name,
                "customer_email": invoice.customer_email,
                "customer_phone": invoice.customer_phone,
                "vendor_id": invoice.vendor_id,
                "vendor_name": invoice.vendor_name,
                "grand_total": invoice.grand_total,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "invoice_date": invoice.invoice_date.isoformat(),
                "service_name": invoice.service_name,
                "channels": channels
            },
            source=EventSource.VENDOR_SERVICE
        )
        logger.info(f"📧 Invoice notification sent: {invoice.invoice_number}")
    except Exception as e:
        logger.error(f"Failed to send invoice notification: {str(e)}")
        # Don't fail the whole operation if notification fails
    
    # Update invoice in MongoDB directly
    now = datetime.utcnow()
    await engine.get_collection(Invoice).update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {
            "status": InvoiceStatus.SENT.value,
            "sent_at": now,
            "updated_at": now
        },
        "$inc": {"sent_count": 1}}
    )
    
    # Fetch updated invoice
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Create audit log
    action = InvoiceAuditAction.RESENT if invoice.sent_count > 1 else InvoiceAuditAction.SENT
    await create_audit_log(
        engine=engine,
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        action=action,
        performed_by=vendor_id,
        notes=notes or f"Sent via {', '.join(channels)}"
    )
    
    return invoice


# ============================================
# Get Invoices
# ============================================

async def get_vendor_invoices(
    engine: AIOEngine,
    vendor_id: str,
    status_filter: Optional[InvoiceStatus] = None,
    customer_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[Invoice]:
    """Get all invoices for vendor with filters"""
    
    # Build MongoDB query to bypass ODMantic validation
    mongo_query = {"vendor_id": vendor_id, "is_active": True}
    
    if status_filter:
        mongo_query["status"] = status_filter.value
    
    if customer_id:
        mongo_query["customer_id"] = customer_id
    
    # Fetch from MongoDB directly
    cursor = engine.get_collection(Invoice).find(mongo_query).sort("created_at", -1).skip(skip).limit(limit)
    raw_invoices = await cursor.to_list(length=limit)
    
    # Map _id to id for each invoice and use model_construct
    invoices = []
    for inv in raw_invoices:
        inv['id'] = inv.pop('_id')
        invoices.append(Invoice.model_construct(**inv))
    
    return invoices


async def get_invoice_by_id(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str
) -> Invoice:
    """Get single invoice by ID"""
    # Fetch directly from MongoDB to bypass ODMantic validation
    raw_invoice = await engine.get_collection(Invoice).find_one({
        "_id": ObjectId(invoice_id),
        "vendor_id": vendor_id
    })
    
    if not raw_invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or access denied"
        )
    
    # Map _id to id for model_construct
    raw_invoice['id'] = raw_invoice.pop('_id')
    
    # Use model_construct to create Invoice object without validation
    invoice = Invoice.model_construct(**raw_invoice)
    return invoice


# ============================================
# Update Invoice
# ============================================

async def update_invoice(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str,
    payload
) -> Invoice:
    """
    Update invoice (only DRAFT status)
    """
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Validate can edit
    if not validate_invoice_edit_allowed(invoice.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit invoice with status {invoice.status}. Only DRAFT invoices can be edited."
        )
    
    # Track changes for audit
    changes = []
    
    # Update fields
    if payload.discount_amount is not None and payload.discount_amount != invoice.discount_amount:
        changes.append(("discount_amount", invoice.discount_amount, payload.discount_amount))
        invoice.discount_amount = payload.discount_amount
    
    if payload.discount_percentage is not None and payload.discount_percentage != invoice.discount_percentage:
        changes.append(("discount_percentage", invoice.discount_percentage, payload.discount_percentage))
        invoice.discount_percentage = payload.discount_percentage
    
    if payload.due_date is not None and payload.due_date != invoice.due_date:
        changes.append(("due_date", invoice.due_date, payload.due_date))
        invoice.due_date = payload.due_date
    
    if payload.notes is not None and payload.notes != invoice.notes:
        changes.append(("notes", invoice.notes, payload.notes))
        invoice.notes = payload.notes
    
    if payload.terms_and_conditions is not None and payload.terms_and_conditions != invoice.terms_and_conditions:
        changes.append(("terms_and_conditions", invoice.terms_and_conditions, payload.terms_and_conditions))
        invoice.terms_and_conditions = payload.terms_and_conditions
    
    # Recalculate totals if discount changed
    if any(field in ["discount_amount", "discount_percentage"] for field, _, _ in changes):
        tax_config = await get_default_tax_config(engine, vendor_id, None)
        totals = calculate_invoice_totals(
            line_items_total=invoice.subtotal,
            discount_amount=invoice.discount_amount,
            discount_percentage=invoice.discount_percentage,
            tax_config=tax_config,
            service_charge_amount=invoice.service_charge,
            other_charges=invoice.other_charges
        )
        
        invoice.total_before_tax = totals['total_before_tax']
        invoice.tax_amount = totals['tax_amount']
        invoice.grand_total = totals['grand_total']
        invoice.balance_due = calculate_balance_due(invoice.grand_total, invoice.paid_amount)
    
    invoice.updated_at = datetime.utcnow()
    await engine.save(invoice)
    
    # Create audit logs for each change
    for field, old_val, new_val in changes:
        await create_audit_log(
            engine=engine,
            invoice_id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            action=InvoiceAuditAction.EDITED,
            performed_by=vendor_id,
            field_changed=field,
            old_value=old_val,
            new_value=new_val
        )
    
    logger.info(f"✏️ Invoice updated: {invoice.invoice_number}")
    return invoice


# ============================================
# Mark Invoice as Paid
# ============================================

async def mark_invoice_paid(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str,
    payload
) -> Invoice:
    """Mark invoice as paid (full or partial)"""
    
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Cannot mark cancelled/refunded as paid
    if invoice.status in [InvoiceStatus.CANCELLED, InvoiceStatus.REFUNDED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark {invoice.status} invoice as paid"
        )
    
    # Calculate new amounts
    new_paid_amount = invoice.paid_amount + payload.paid_amount
    new_balance_due = calculate_balance_due(invoice.grand_total, new_paid_amount)
    
    # Determine new status
    if new_balance_due <= 0:
        new_status = InvoiceStatus.PAID.value
        payment_received_at = payload.payment_date or datetime.utcnow()
    else:
        new_status = InvoiceStatus.PARTIALLY_PAID.value
        payment_received_at = None
    
    # Update in MongoDB directly
    now = datetime.utcnow()
    update_doc = {
        "paid_amount": new_paid_amount,
        "balance_due": new_balance_due,
        "status": new_status,
        "payment_method": payload.payment_method,
        "payment_reference": payload.payment_reference,
        "updated_at": now
    }
    if payment_received_at:
        update_doc["payment_received_at"] = payment_received_at
    
    await engine.get_collection(Invoice).update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": update_doc}
    )
    
    # Fetch updated invoice
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Create audit log
    await create_audit_log(
        engine=engine,
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        action=InvoiceAuditAction.PAYMENT_RECEIVED,
        performed_by=vendor_id,
        notes=f"Payment received: ₹{payload.paid_amount} via {payload.payment_method}. Reference: {payload.payment_reference or 'N/A'}"
    )
    
    logger.info(f"💰 Payment recorded for invoice {invoice.invoice_number}: ₹{payload.paid_amount}")
    return invoice


# ============================================
# Cancel Invoice
# ============================================

async def cancel_invoice(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str,
    reason: str
) -> Invoice:
    """Cancel invoice"""
    
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Validate can cancel
    if not validate_invoice_cancel_allowed(invoice.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel invoice with status {invoice.status}"
        )
    
    # Update in MongoDB directly
    now = datetime.utcnow()
    await engine.get_collection(Invoice).update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {
            "status": InvoiceStatus.CANCELLED.value,
            "cancelled_at": now,
            "cancellation_reason": reason,
            "cancelled_by": vendor_id,
            "updated_at": now
        }}
    )
    
    # Fetch updated invoice
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Create audit log
    await create_audit_log(
        engine=engine,
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        action=InvoiceAuditAction.CANCELLED,
        performed_by=vendor_id,
        reason=reason
    )
    
    logger.info(f"❌ Invoice cancelled: {invoice.invoice_number}")
    return invoice


# ============================================
# Get Audit Logs
# ============================================

async def get_invoice_audit_logs(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str
) -> List[InvoiceAuditLog]:
    """Get all audit logs for an invoice"""
    
    # Verify invoice belongs to vendor
    await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    logs = await engine.find(
        InvoiceAuditLog,
        InvoiceAuditLog.invoice_id == invoice_id,
        sort=InvoiceAuditLog.timestamp.desc()
    )
    
    return logs
