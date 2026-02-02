"""
WhatsApp Notification Handler
Sends messages via Twilio WhatsApp Business API
"""
from typing import Dict, Any
import logging
import aiohttp
import base64

from notifications.handlers.base import BaseNotificationHandler
from core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppHandler(BaseNotificationHandler):
    """
    Handles WhatsApp notifications via Twilio API
    Used for important updates and confirmations
    """
    
    def __init__(self):
        super().__init__()
        self.account_sid = settings.WHATSAPP_ACCOUNT_SID
        self.auth_token = settings.WHATSAPP_AUTH_TOKEN
        self.from_number = settings.WHATSAPP_FROM_NUMBER
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """Validate WhatsApp number is present"""
        whatsapp = notification_data.get("recipient_whatsapp")
        return bool(whatsapp and whatsapp.startswith("+"))
    
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio API
        
        Raises exception on failure (will trigger retry)
        """
        try:
            # Validate
            if not self.validate_recipient(notification_data):
                raise ValueError("recipient_whatsapp (with +country code) is required")
            
            recipient_whatsapp = notification_data["recipient_whatsapp"]
            notification_id = notification_data.get("notification_id")
            
            # Ensure whatsapp: prefix
            if not recipient_whatsapp.startswith("whatsapp:"):
                recipient_whatsapp = f"whatsapp:{recipient_whatsapp}"
            
            # Prepare content
            message = await self.prepare_content(notification_data)
            
            # Check if credentials are configured
            if not self.account_sid or not self.auth_token or self.account_sid == "":
                # Mock mode for testing without credentials
                logger.warning(f"💬 [MOCK] Would send WhatsApp to {recipient_whatsapp}")
                logger.info(f"   Message: {message[:100]}...")
                
                metadata = {
                    "recipient": recipient_whatsapp,
                    "message_length": len(message),
                    "mode": "mock"
                }
            else:
                # Real Twilio API call
                auth_str = f"{self.account_sid}:{self.auth_token}"
                auth_bytes = auth_str.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                
                headers = {
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                data = {
                    "From": self.from_number,
                    "To": recipient_whatsapp,
                    "Body": message
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_data = await response.json()
                        
                        if response.status not in [200, 201]:
                            error = response_data.get("message", "Unknown error")
                            raise Exception(f"Twilio API error: {error}")
                        
                        metadata = {
                            "recipient": recipient_whatsapp,
                            "message_sid": response_data.get("sid"),
                            "status": response_data.get("status"),
                            "mode": "twilio"
                        }
            
            self.log_success(notification_id, metadata)
            
            return {
                "success": True,
                "message": f"WhatsApp sent to {recipient_whatsapp}",
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Failed to send WhatsApp: {str(e)}"
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
