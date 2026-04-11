import asyncio
from core.database import get_engine
from vendor.models.invoice import Invoice
from notifications.services.pdf_service import pdf_service

async def main():
    engine = get_engine()
    invoice = await engine.find_one(Invoice, sort=Invoice.created_at.desc())
    if not invoice:
        print("No invoice found!")
        return

    from datetime import datetime
    event_data = {
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.strftime("%Y-%m-%d"),
        "vendor_name": "Test Vendor",
        "customer_name": "Test Customer",
        "grand_total": invoice.grand_total,
        "items": [item.model_dump() for item in invoice.items] if invoice.items else []
    }
    
    pdf_content = pdf_service.generate_invoice_pdf(event_data)
    with open("test.pdf", "wb") as f:
        f.write(pdf_content)
    print("Dumped test.pdf")

asyncio.run(main())
