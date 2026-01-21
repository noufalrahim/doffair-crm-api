"""
SMS Notification Handler
Sends SMS via 2Factor API
"""
from typing import Dict, Any
import logging
import aiohttp

from notifications.handlers.base import BaseNotificationHandler
from core.config import settings

logger = logging.getLogger(__name__)


class SMSHandler(BaseNotificationHandler):
    """
    Handles SMS notifications via 2Factor API
    Used for OTPs and important alerts
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = settings.TWOFACTOR_API_KEY
        self.api_url = "https://2factor.in/API/V1/{api_key}/SMS/{phone}/{otp}/{template}"
        self.template_name = settings.TWOFACTOR_OTP_TEMPLATE
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """Validate phone number is present"""
        phone = notification_data.get("recipient_phone")
        return bool(phone and phone.startswith("+"))
    
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS via 2Factor API
        
        Raises exception on failure (will trigger retry)
        """
        try:
            # Validate
            if not self.validate_recipient(notification_data):
                raise ValueError("recipient_phone (with +country code) is required for SMS")
            
            recipient_phone = notification_data["recipient_phone"]
            notification_id = notification_data.get("notification_id")
            
            # Remove + prefix for 2Factor API
            phone_number = recipient_phone.lstrip("+")
            
            # Prepare content
            message = await self.prepare_content(notification_data)
            
            # Extract OTP if present in data
            otp = notification_data.get("data", {}).get("otp", "123456")
            
            # Check if API key is configured and valid
            if not self.api_key or self.api_key == "" or self.api_key == "your_api_key_here":
                # Mock mode for testing without API key
                logger.warning(f"📱 [MOCK] Would send SMS to {recipient_phone}")
                logger.info(f"   Message: {message[:100]}...")
                
                metadata = {
                    "recipient": recipient_phone,
                    "message_length": len(message),
                    "mode": "mock"
                }
            else:
                # Real 2Factor API call
                url = self.api_url.format(
                    api_key=self.api_key,
                    phone=phone_number,
                    otp=otp,
                    template=self.template_name
                )
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response_data = await response.json()
                        
                        if response.status != 200 or response_data.get("Status") != "Success":
                            raise Exception(f"2Factor API error: {response_data}")
                        
                        metadata = {
                            "recipient": recipient_phone,
                            "session_id": response_data.get("Details"),
                            "mode": "2factor"
                        }
            
            self.log_success(notification_id, metadata)
            
            return {
                "success": True,
                "message": f"SMS sent to {recipient_phone}",
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Failed to send SMS: {str(e)}"
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
