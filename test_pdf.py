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
    
    # Parse dates just like simple_worker.py does
    for field in ["invoice_date", "due_date"]:
        val = event_data.get(field)
        if isinstance(val, str) and val and val != "N/A":
            try:
                event_data[field] = datetime.fromisoformat(val.split("T")[0] if "T" in val else val)
            except Exception:
                pass

    pdf_content = pdf_service.generate_invoice_pdf(event_data)
    if pdf_content:
        print(f"PDF Size: {len(pdf_content)} bytes")
    else:
        print("PDF Generation FAILED")

asyncio.run(main())
