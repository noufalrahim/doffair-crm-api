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
from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from user.models.user import User
from vendor.schemas.invoice import (
    InvoiceCreateRequest, 
    InvoiceUpdateRequest,
    InvoiceStatisticsResponse,
    InvoiceItemSchema
)
from core.enums import InvoiceStatus
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource

logger = logging.getLogger(__name__)

async def calculate_invoice_totals(items: List[InvoiceItem], tax_amount_input: float = 0.0, discount_amount_input: float = 0.0) -> dict:
    """
    Calculate taxable value, tax breakdown, and rounding off.
    Matches the logic in the sample PDF.
    """
    tax_details = {}
    total_tax_amount = 0.0
    total_taxable_value = 0.0
    total_amount = 0.0
    total_mrp = 0.0

    for item in items:
        # If tax_rate is provided but tax_amount is not, calculate it
        if item.tax_rate > 0 and item.tax_amount == 0:
            # item.unit_price is usually the price AFTER discount but BEFORE tax in some systems, 
            # but let's assume item.unit_price is the taxable value per unit for simplicity here 
            # or calculate based on the provided sample logic.
            item.taxable_value = item.unit_price * item.quantity
            item.tax_amount = round(item.taxable_value * (item.tax_rate / 100), 2)
        
        item.subtotal = item.taxable_value + item.tax_amount
        
        total_taxable_value += item.taxable_value
        total_tax_amount += item.tax_amount
        total_amount += item.subtotal
        total_mrp += (item.mrp or 0.0) * item.quantity

        # Tax breakdown (SGST/CGST)
        if item.tax_rate > 0:
            half_rate = item.tax_rate / 2
            half_tax = item.tax_amount / 2
            
            sgst_key = f"sgst {half_rate}%"
            cgst_key = f"cgst {half_rate}%"
            
            tax_details[sgst_key] = tax_details.get(sgst_key, 0.0) + half_tax
            tax_details[cgst_key] = tax_details.get(cgst_key, 0.0) + half_tax

    # Final adjustments
    grand_total_raw = total_amount + tax_amount_input - discount_amount_input
    grand_total = round(grand_total_raw)
    rounding_off = round(grand_total - grand_total_raw, 2)

    return {
        "tax_amount": round(total_tax_amount + tax_amount_input, 2),
        "total_taxable_value": round(total_taxable_value, 2),
        "total_mrp": round(total_mrp, 2),
        "grand_total": float(grand_total),
        "rounding_off": rounding_off,
        "tax_details": {k: round(v, 2) for k, v in tax_details.items()}
    }


def num_to_words(n: float) -> str:
    """Convert number to words in Indian currency format"""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_less_than_thousand(num):
        res = ""
        if num >= 100:
            res += units[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            res += tens[num // 10] + " "
            num %= 10
        elif num >= 10:
            res += teens[num - 10] + " "
            num = 0
        if num > 0:
            res += units[num] + " "
        return res

    n_int = int(n)
    if n_int == 0: return "Zero Rupees Only"
    
    res = ""
    # Crores
    if n_int >= 10000000:
        res += convert_less_than_thousand(n_int // 10000000) + "Crore "
        n_int %= 10000000
    # Lakhs
    if n_int >= 100000:
        res += convert_less_than_thousand(n_int // 100000) + "Lakh "
        n_int %= 100000
    # Thousands
    if n_int >= 1000:
        res += convert_less_than_thousand(n_int // 1000) + "Thousand "
        n_int %= 1000
    # Rest
    res += convert_less_than_thousand(n_int)
    
    return res.strip().upper() + " RUPEES ONLY"


async def create_invoice(engine: AIOEngine, vendor_id: str, payload: InvoiceCreateRequest) -> Invoice:
    """Create a new itemized invoice with detailed data population"""
    invoice_number = await generate_unique_invoice_number(engine, vendor_id)
    
    # Fetch Vendor and Booking data
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    booking = None
    location = None
    if payload.booking_id:
        try:
            booking = await engine.find_one(Booking, Booking.id == ObjectId(payload.booking_id))
            if booking and booking.location_id:
                location = await engine.find_one(VendorLocation, VendorLocation.id == ObjectId(booking.location_id))
        except Exception:
            pass

    # Fetch User data
    user = await engine.find_one(User, User.id == ObjectId(payload.customer_id))
            
    # Process items
    invoice_items = []
    if not payload.items and booking:
        # Auto-generate item from booking if no items provided
        invoice_items.append(InvoiceItem(
            name=booking.service_name,
            quantity=1,
            unit_price=booking.base_amount - booking.discount_amount,
            mrp=booking.base_amount,
            taxable_value=booking.base_amount - booking.discount_amount,
            tax_rate=18.0, # Defaulting to 18% as per sample
        ))
    else:
        for item in payload.items:
            invoice_items.append(InvoiceItem(
                name=item.name,
                hsn_sac=item.hsn_sac,
                mrp=item.mrp or item.unit_price,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                taxable_value=item.taxable_value or (item.unit_price * item.quantity),
                tax_rate=item.tax_rate,
                tax_amount=item.tax_amount
            ))
        
    # Calculate totals
    totals = await calculate_invoice_totals(
        invoice_items, 
        payload.tax_amount, 
        payload.discount_amount
    )
    
    # Use payload grand_total if provided (manual override), otherwise use calculated
    grand_total = payload.grand_total if payload.grand_total is not None else totals["grand_total"]
            
    # Map vendor address
    vendor_address = ""
    if location:
        vendor_address = f"{location.address_line_1}, {location.address_line_2 or ''}, {location.city}, {location.state} - {location.pincode}"
    
    invoice = Invoice(
        vendor_id=vendor_id,
        customer_id=payload.customer_id,
        booking_id=payload.booking_id,
        vertical_id=payload.vertical_id or (booking.vertical_id if booking else None),
        invoice_number=invoice_number,
        due_date=payload.due_date,
        
        # Cached details
        vendor_name=vendor.legal_name if vendor else "Vendor",
        vendor_address=vendor_address,
        vendor_gstin=vendor.gst_number if vendor else None,
        vendor_phone=vendor.primary_contact_phone if vendor else None,
        
        customer_name=user.name if user else (booking.user_name if booking else "Customer"),
        customer_phone=user.phone if user else (booking.user_phone if booking else ""),
        customer_pincode=booking.service_pincode if booking else None,
        
        items=invoice_items,
        notes=payload.notes,
        tax_amount=totals["tax_amount"],
        discount_amount=payload.discount_amount,
        rounding_off=totals["rounding_off"],
        grand_total=grand_total,
        grand_total_words=num_to_words(grand_total),
        paid_amount=0.0,
        balance_due=grand_total,
        tax_details=totals["tax_details"],
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


