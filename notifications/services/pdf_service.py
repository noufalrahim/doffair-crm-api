import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from core.config import settings

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates" / "INVOICE_SENT" / "user"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def generate_invoice_pdf(self, invoice_data: Dict[str, Any], template_name="invoice_pdf.html") -> Optional[bytes]:
        """
        Generates a PDF from invoice data using an HTML template.
        """
        try:
            # 1. Load and render template
            template = self.env.get_template(template_name)
            
            # Ensure all numeric fields are formatted if needed, 
            # or pass them as is for Jinja2 filters
            html_content = template.render(**invoice_data)

            # 2. Convert HTML to PDF
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
