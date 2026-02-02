"""
Email Notification Handler
Sends emails via SMTP (Gmail, SendGrid, SES, etc.)
"""
from typing import Dict, Any
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from notifications.handlers.base import BaseNotificationHandler
from core.config import settings

logger = logging.getLogger(__name__)


class EmailHandler(BaseNotificationHandler):
    """
    Handles email notifications via SMTP
    Supports HTML and plain text emails
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
            
            # Prepare content
            subject = notification_data.get("subject", "Notification from Doffair")
            body = await self.prepare_content(notification_data)
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add plain text version
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML version if template data exists
            html_body = self._create_html_body(notification_data)
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Send email via SMTP
            if not self.smtp_username or not self.smtp_password:
                # Mock mode for testing without credentials
                logger.warning(f"📧 [MOCK] Would send email to {recipient_email}")
                logger.info(f"   Subject: {subject}")
                logger.info(f"   Body: {body[:100]}...")
                
                metadata = {
                    "recipient": recipient_email,
                    "subject": subject,
                    "mode": "mock"
                }
            else:
                # Real SMTP sending
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    start_tls=True
                )
                
                metadata = {
                    "recipient": recipient_email,
                    "subject": subject,
                    "smtp_host": self.smtp_host,
                    "mode": "smtp"
                }
            
            self.log_success(notification_id, metadata)
            
            return {
                "success": True,
                "message": f"Email sent to {recipient_email}",
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
    
    def _create_html_body(self, notification_data: Dict[str, Any]) -> str:
        """
        Create HTML email body from template
        Simple version - can be enhanced with Jinja2 templates
        """
        template_id = notification_data.get("template_id")
        data = notification_data.get("data", {})
        subject = notification_data.get("subject", "")
        message = notification_data.get("message", "")
        
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
        if template_id == "BOOKING_CONFIRMED" and data:
            html += f"""
                    <p><strong>Booking Details:</strong></p>
                    <ul>
                        <li>Booking ID: {data.get('booking_id', 'N/A')}</li>
                        <li>Service: {data.get('service_name', 'N/A')}</li>
                        <li>Date: {data.get('booking_date', 'N/A')}</li>
                        <li>Vendor: {data.get('vendor_name', 'N/A')}</li>
                    </ul>
            """
        
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
