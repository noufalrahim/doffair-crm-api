"""
Email Notification Handler
Sends emails via SMTP (Gmail, SendGrid, SES, etc.)
"""
from typing import Dict, Any, List, Optional
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
import logging

from notifications.handlers.base import BaseNotificationHandler
from core.config import settings

logger = logging.getLogger(__name__)


class EmailHandler(BaseNotificationHandler):
    """
    Handles email notifications via SMTP
    Supports HTML and plain text emails, and attachments
    """
    
    def __init__(self):
        super().__init__()
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """Validate email address is present"""
        return bool(notification_data.get("recipient_email"))
    
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email via SMTP
        
        Raises exception on failure (will trigger retry)
        """
        try:
            # Validate
            if not self.validate_recipient(notification_data):
                raise ValueError("recipient_email is required for email notifications")
            
            recipient_email = notification_data["recipient_email"]
            notification_id = notification_data.get("notification_id")
            attachments = notification_data.get("attachments", [])
            
            # Prepare content
            subject = notification_data.get("subject", "Notification from Doffair")
            body = await self.prepare_content(notification_data)
            notification_data["message"] = body # Ensure content is available for HTML renderer
            html_body = self._create_html_body(notification_data)
            
            # Create email message
            if attachments:
                message = MIMEMultipart("mixed")
            else:
                message = MIMEMultipart("alternative")
                
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Create body part
            if attachments:
                body_multipart = MIMEMultipart("alternative")
                body_multipart.attach(MIMEText(body, "plain"))
                if html_body:
                    body_multipart.attach(MIMEText(html_body, "html"))
                message.attach(body_multipart)
                
                # Add attachments
                for att in attachments:
                    part = MIMEApplication(att["content"])
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=att["filename"]
                    )
                    message.attach(part)
            else:
                # Standard simple email
                message.attach(MIMEText(body, "plain"))
                if html_body:
                    message.attach(MIMEText(html_body, "html"))
            
            # Send email via SMTP
            if not self.smtp_username or not self.smtp_password:
                # Mock mode for testing without credentials
                logger.warning(f"📧 [MOCK] Would send email to {recipient_email}")
                logger.info(f"   Subject: {subject}")
                logger.info(f"   Body: {body[:100]}...")
                if attachments:
                    logger.info(f"   Attachments: {[a['filename'] for a in attachments]}")
                
                metadata = {
                    "recipient": recipient_email,
                    "subject": subject,
                    "mode": "mock",
                    "has_attachments": bool(attachments)
                }
            else:
                # Real SMTP sending
                logger.info(f"📧 Attempting to send email to {recipient_email} via {self.smtp_host}:{self.smtp_port}")
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    start_tls=True
                )
                
                logger.info(f"✅ Email successfully sent to {recipient_email}")
                metadata = {
                    "recipient": recipient_email,
                    "subject": subject,
                    "smtp_host": self.smtp_host,
                    "mode": "smtp",
                    "has_attachments": bool(attachments)
                }
            
            self.log_success(notification_id, metadata)
            
            return {
                "success": True,
                "message": f"Email sent to {recipient_email}",
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"❌ Failed to send email to {recipient_email if 'recipient_email' in locals() else 'unknown'}: {str(e)}"
            logger.error(error_msg)
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
    
    def _create_html_body(self, notification_data: Dict[str, Any]) -> str:
        """
        Create HTML email body from template
        Simple version - can be enhanced with Jinja2 templates
        """
        data = notification_data.get("data", {})
        template_id = notification_data.get("template_id") or data.get("template_id")
        subject = notification_data.get("subject", "")
        message = notification_data.get("message", "")
        
        # If message is already a full HTML document, return it as is
        if message and (message.strip().startswith("<!DOCTYPE html>") or message.strip().startswith("<html")):
            return message
            
        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Doffair</h1>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{message}</p>
        """
        
        # Add template-specific content
        if template_id == "INVOICE_SENT" or data.get("invoice_number"):
            html += f"""
                    <p><strong>Invoice Details:</strong></p>
                    <ul>
                        <li>Invoice Number: {data.get('invoice_number', 'N/A')}</li>
                        <li>Total Amount: {data.get('grand_total', 'N/A')}</li>
                        <li>Due Date: {data.get('due_date', 'N/A')}</li>
                        <li>Vendor: {data.get('vendor_name', 'Doffair Vendor')}</li>
                    </ul>
                    <p>Please find your invoice attached as a PDF.</p>
            """
        elif template_id == "BOOKING_CONFIRMED" and data:
            html += f"""
                    <p><strong>Booking Details:</strong></p>
                    <ul>
                        <li>Booking ID: {data.get('booking_id', 'N/A')}</li>
                        <li>Service: {data.get('service_name', 'N/A')}</li>
                        <li>Date: {data.get('booking_date', 'N/A')}</li>
                        <li>Vendor: {data.get('vendor_name', 'N/A')}</li>
                    </ul>
            """
        elif template_id in ["SERVICE_START_OTP", "ONBOARDING_OTP"]:
            otp_code = data.get('otp_code') or data.get('var2') or '----'
            html += f"""
                    <div style="text-align: center; margin: 40px 0; padding: 30px; background-color: #fff; border: 2px dashed #4CAF50; border-radius: 10px;">
                        <p style="margin: 0; font-size: 16px; color: #666; text-transform: uppercase; letter-spacing: 2px;">Your Verification Code</p>
                        <h1 style="margin: 15px 0 0 0; font-size: 64px; color: #4CAF50; letter-spacing: 12px; font-weight: bold;">{otp_code}</h1>
                    </div>
                    <p style="text-align: center; font-size: 15px; color: #555;">Please provide this code to verify your account. Valid for 10 minutes.</p>
            """
            html += "</div>" # close content
            html += """
                <div class="footer">
                    <p>&copy; 2026 Doffair. All rights reserved.</p>
                </div>
            </div>
            </body>
            </html>
            """
            return html

        elif data:
            # Generic catch-all for other data
            html += "<p><strong>Details:</strong></p><ul>"
            # Limit to 5 fields to avoid huge emails
            for key, val in list(data.items())[:5]:
                if key not in ["id", "_id", "user_id", "vendor_id"]:
                    html += f"<li>{key.replace('_', ' ').title()}: {val}</li>"
            html += "</ul>"
        
        html += """
                </div>
                <div class="footer">
                    <p>&copy; 2026 Doffair. All rights reserved.</p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
