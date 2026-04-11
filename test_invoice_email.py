import asyncio
from core.database import get_engine
from vendor.models.invoice import Invoice
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource
import logging

async def main():
    engine = get_engine()
    invoice = await engine.find_one(Invoice, sort=Invoice.created_at.desc())
    if not invoice:
        print("No invoice found!")
        return

    print(f"Triggering email for invoice {invoice.invoice_number}")
    
    event_data = {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.strftime("%Y-%m-%d"),
        "vendor_id": invoice.vendor_id,
        "customer_id": invoice.customer_id,
        "user_id": invoice.customer_id,
        "customer_name": invoice.customer_name or "Customer",
        "user_name": invoice.customer_name or "Customer",
        "user_phone": invoice.customer_phone or "",
        "user_email": "noufalrahim0444@gmail.com",
        "grand_total": f"{invoice.grand_total:,.2f}",
        "balance_due": f"{invoice.balance_due:,.2f}",
        "due_date": invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A",
        "service_name": invoice.items[0].name if invoice.items else "Service",
        "service_date": invoice.invoice_date.strftime("%Y-%m-%d"),
        "vendor_name": invoice.vendor_name or "Doffair Vendor",
        "vendor_phone": invoice.vendor_phone or "",
        "vendor_email": "",
        "items": [item.model_dump() for item in invoice.items] if invoice.items else [],
        "tax_details": invoice.tax_details or {},
        "rounding_off": invoice.rounding_off or 0.0,
        "grand_total_words": invoice.grand_total_words or "",
        "template_id": "InvoiceSent"
    }

    event_publisher.publish(
        event_type=EventType.INVOICE_SENT,
        source=EventSource.VENDOR_SERVICE,
        data=event_data
    )
    print("Done")

asyncio.run(main())
