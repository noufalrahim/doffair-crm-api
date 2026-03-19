import random
import string
from datetime import datetime
from typing import Optional, List, Tuple
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

import random
import string
from datetime import datetime
from typing import Optional, List, Tuple
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from vendor.models.invoice import Invoice, InvoiceItem
from user.models.booking import Booking
from vendor.schemas.invoice import (
    InvoiceCreateRequest, 
    InvoiceUpdateRequest,
    InvoiceStatisticsResponse,
    InvoiceItemSchema
)
from core.enums import InvoiceStatus
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource
from user.models.user import User

logger = logging.getLogger(__name__)



async def generate_unique_invoice_number(engine: AIOEngine, vendor_id: str) -> str:
    """
    Generate a random autoincrement style invoice number.
    Format: INV-{sequence}-{random4}
    """
    # Get the current count of invoices to act as the incrementing part
    count = await engine.count(Invoice, Invoice.vendor_id == vendor_id)
    sequence = count + 1
    
    attempts = 0
    while attempts < 10:
        rand_part = ''.join(random.choices(string.digits, k=4))
        invoice_number = f"INV-{sequence:04d}-{rand_part}"
        
        # Check for uniqueness
        exists = await engine.find_one(Invoice, Invoice.invoice_number == invoice_number)
        if not exists:
            return invoice_number
        attempts += 1
    
    # Fallback to a timestamp if collision persists
    return f"INV-{sequence:04d}-{int(datetime.utcnow().timestamp()) % 10000:04d}"


async def create_invoice(engine: AIOEngine, vendor_id: str, payload: InvoiceCreateRequest) -> Invoice:
    """Create a new itemized invoice"""
    invoice_number = await generate_unique_invoice_number(engine, vendor_id)
    
    # Fetch vertical_id from booking if not provided
    vertical_id = payload.vertical_id
    if not vertical_id and payload.booking_id:
        try:
            booking = await engine.find_one(Booking, Booking.id == ObjectId(payload.booking_id))
            if booking:
                vertical_id = booking.vertical_id
        except Exception:
            pass
            
    # Process items and calculate totals
    invoice_items = []
    calculated_grand_total = 0.0
    
    for item in payload.items:
        subtotal = item.quantity * item.unit_price
        invoice_items.append(InvoiceItem(
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=subtotal
        ))
        calculated_grand_total += subtotal
        
    # Apply taxes and discounts
    calculated_grand_total += payload.tax_amount
    calculated_grand_total -= payload.discount_amount
    calculated_grand_total = max(0.0, calculated_grand_total)
    
    # Use payload grand_total if provided (manual override), otherwise use calculated
    grand_total = payload.grand_total if payload.grand_total is not None else calculated_grand_total
            
    invoice = Invoice(
        vendor_id=vendor_id,
        customer_id=payload.customer_id,
        booking_id=payload.booking_id,
        vertical_id=vertical_id,
        invoice_number=invoice_number,
        due_date=payload.due_date,
        items=invoice_items,
        notes=payload.notes,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        grand_total=grand_total,
        paid_amount=0.0,
        balance_due=grand_total,
        status=InvoiceStatus.DRAFT
    )
    
    await engine.save(invoice)
    logger.info(f"✅ Itemized Invoice created: {invoice_number}")
    return invoice


async def get_invoice_by_id(engine: AIOEngine, vendor_id: str, invoice_id: str) -> Invoice:
    """Get an invoice by ID"""
    try:
        invoice = await engine.find_one(
            Invoice, 
            (Invoice.id == ObjectId(invoice_id)) & (Invoice.vendor_id == vendor_id)
        )
    except Exception:
        invoice = None
        
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


async def list_invoices(
    engine: AIOEngine,
    vendor_id: str,
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None,
    vertical_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Invoice], int]:
    """List invoices with filters"""
    query = [Invoice.vendor_id == vendor_id]
    
    if customer_id:
        query.append(Invoice.customer_id == customer_id)
    if status:
        query.append(Invoice.status == status)
    if vertical_id:
        query.append(Invoice.vertical_id == vertical_id)
        
    invoices = await engine.find(
        Invoice,
        *query,
        sort=Invoice.created_at.desc(),
        skip=skip,
        limit=limit
    )
    total = await engine.count(Invoice, *query)
    
    return invoices, total


async def update_invoice(
    engine: AIOEngine, 
    vendor_id: str, 
    invoice_id: str, 
    payload: InvoiceUpdateRequest
) -> Invoice:
    """Update an invoice and recalculate balance_due if needed"""
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(invoice, key, value)
        
    # Recalculate balance due
    invoice.balance_due = max(0.0, invoice.grand_total - invoice.paid_amount)
    
    # Auto-update status to PAID if balance is 0 and it was previously partially paid or sent
    if invoice.balance_due == 0 and invoice.status in [InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]:
        invoice.status = InvoiceStatus.PAID
        
    invoice.updated_at = datetime.utcnow()
    await engine.save(invoice)
    
    if invoice.status == InvoiceStatus.SENT:
        # Trigger Notification
        # We need to fetch the customer/user to get their phone/email if not in payload
        user = await engine.find_one(User, User.id == ObjectId(invoice.customer_id))
        
        event_publisher.publish(
            event_type=EventType.INVOICE_SENT,
            source=EventSource.VENDOR_SERVICE,
            data={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "vendor_id": invoice.vendor_id,
                "customer_id": invoice.customer_id,
                "user_id": invoice.customer_id,
                "user_name": user.username if user else "Customer",
                "user_phone": user.phoneNumber if user else "",
                "user_email": user.email if user else "",
                "grand_total": invoice.grand_total,
                "due_date": invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A",
                "vendor_name": "Doffair Vendor", # Ideally fetch vendor name
                "template_id": "InvoiceSent"
            }
        )

    logger.info(f"✏️ Invoice updated: {invoice.invoice_number}")
    return invoice


async def delete_invoice(engine: AIOEngine, vendor_id: str, invoice_id: str) -> bool:
    """Hard delete an invoice"""
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    await engine.delete(invoice)
    logger.info(f"🗑️ Invoice deleted: {invoice.invoice_number}")
    return True


async def get_invoice_statistics(
    engine: AIOEngine, 
    vendor_id: str, 
    vertical_id: Optional[str] = None
) -> InvoiceStatisticsResponse:
    """
    Get financial statistics for a vendor, optionally filtered by vertical
    """
    query = [Invoice.vendor_id == vendor_id]
    if vertical_id:
        query.append(Invoice.vertical_id == vertical_id)
        
    invoices = await engine.find(Invoice, *query)
    
    stats = {
        "total_earnings": sum(inv.paid_amount for inv in invoices),
        "total_bookings": len(set(inv.booking_id for inv in invoices if inv.booking_id)),
        "total_generated": sum(1 for inv in invoices if inv.status == InvoiceStatus.GENERATED),
        "total_paid": sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID),
        "total_refunded": sum(1 for inv in invoices if inv.status == InvoiceStatus.REFUNDED),
        "total_overdue": sum(1 for inv in invoices if inv.status == InvoiceStatus.OVERDUE)
    }
    
    return InvoiceStatisticsResponse(**stats)


