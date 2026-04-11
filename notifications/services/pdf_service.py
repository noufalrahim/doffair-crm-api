import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from core.config import settings

logger = logging.getLogger(__name__)


def _safe_float(val, default=0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def prepare_invoice_pdf_data(invoice_model_dict: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine the raw Invoice model_dump() with enriched event_data fields
    to produce a template-ready context dict for invoice_pdf.html.

    The Jinja2 template (invoice_pdf.html) expects:
      - invoice_number, invoice_date (datetime obj), due_date (datetime or None)
      - vendor_name, vendor_address, vendor_phone, vendor_gstin
      - customer_name, customer_phone
      - items: list of dicts with name, mrp, quantity, taxable_value, tax_rate, tax_amount, subtotal, discount_amount, hsn_sac
      - tax_details: dict
      - rounding_off, grand_total, grand_total_words
      - status
    """
    # Parse invoice_date — model_dump() returns datetime for model fields but event_data has strings
    invoice_date = invoice_model_dict.get("invoice_date") or invoice_model_dict.get("created_at")
    if isinstance(invoice_date, str):
        try:
            invoice_date = datetime.fromisoformat(invoice_date.replace("Z", "+00:00"))
        except Exception:
            invoice_date = datetime.utcnow()
    elif invoice_date is None:
        invoice_date = datetime.utcnow()

    due_date = invoice_model_dict.get("due_date")
    if isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except Exception:
            due_date = None

    # Normalise items: items from model_dump() are already dicts with the right field names
    raw_items = invoice_model_dict.get("items") or []
    items = []
    for item in raw_items:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        items.append({
            "name": item.get("name", "Service"),
            "hsn_sac": item.get("hsn_sac", ""),
            "mrp": _safe_float(item.get("mrp")),
            "quantity": item.get("quantity", 1),
            "unit_price": _safe_float(item.get("unit_price")),
            "discount_amount": _safe_float(item.get("discount_amount")),
            "taxable_value": _safe_float(item.get("taxable_value")),
            "tax_rate": _safe_float(item.get("tax_rate")),
            "tax_amount": _safe_float(item.get("tax_amount")),
            "subtotal": _safe_float(item.get("subtotal")),
        })

    # Prefer event_data values for display fields (more complete / enriched)
    return {
        "invoice_number": event_data.get("invoice_number") or invoice_model_dict.get("invoice_number", ""),
        "invoice_date": invoice_date,
        "due_date": due_date,

        "vendor_name": event_data.get("vendor_name") or invoice_model_dict.get("vendor_name", "Doffair Vendor"),
        "vendor_address": invoice_model_dict.get("vendor_address", ""),
        "vendor_phone": event_data.get("vendor_phone") or invoice_model_dict.get("vendor_phone", ""),
        "vendor_gstin": invoice_model_dict.get("vendor_gstin", ""),

        "customer_name": event_data.get("customer_name") or invoice_model_dict.get("customer_name", "Customer"),
        "customer_phone": event_data.get("user_phone") or invoice_model_dict.get("customer_phone", ""),

        "items": items,
        "tax_details": invoice_model_dict.get("tax_details") or {},
        "rounding_off": _safe_float(invoice_model_dict.get("rounding_off")),
        "grand_total": _safe_float(event_data.get("grand_total") or invoice_model_dict.get("grand_total")),
        "grand_total_words": invoice_model_dict.get("grand_total_words", ""),

        "paid_amount": _safe_float(invoice_model_dict.get("paid_amount")),
        "balance_due": _safe_float(event_data.get("balance_due") or invoice_model_dict.get("balance_due")),

        "status": invoice_model_dict.get("status", ""),
        "notes": invoice_model_dict.get("notes", ""),
    }


class PDFService:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates" / "INVOICE_SENT" / "user"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def generate_invoice_pdf(self, invoice_data: Dict[str, Any], template_name="invoice_pdf.html") -> Optional[bytes]:
        """
        Generates a PDF from invoice data using an HTML template.
        `invoice_data` should be the output of `prepare_invoice_pdf_data()` for best results,
        or a raw invoice model_dump() as fallback.
        """
        try:
            # Load and render template
            template = self.env.get_template(template_name)
            html_content = template.render(**invoice_data)

            # Convert HTML to PDF
            pdf_buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(
                io.StringIO(html_content),
                dest=pdf_buffer
            )

            if pisa_status.err:
                logger.error(f"❌ PDF generation failed: {pisa_status.err}")
                return None

            return pdf_buffer.getvalue()

        except Exception as e:
            logger.error(f"❌ Error generating PDF: {str(e)}")
            return None


pdf_service = PDFService()
