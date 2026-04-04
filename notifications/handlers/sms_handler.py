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
        self.api_url = settings.TWOFACTOR_API_URL
        self.sender_id = settings.TWOFACTOR_SENDER_ID
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """Validate phone number is present"""
        phone = notification_data.get("recipient_phone")
        return bool(phone)
    
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS via 2Factor R1 API (Transactional)
        
        Raises exception on failure (will trigger retry)
        """
        try:
            # Validate
            if not self.validate_recipient(notification_data):
                raise ValueError("recipient_phone is required for SMS")
            
            recipient_phone = notification_data["recipient_phone"]
            notification_id = notification_data.get("notification_id")
            
            # Remove + prefix for 2Factor API if present
            phone_number = str(recipient_phone).lstrip("+")
            
            # Extract template name from data or use a default based on event_type
            template_name = notification_data.get("template_id")
            
            # Check if API key is configured
            if not self.api_key or self.api_key in ["", "your_api_key_here"]:
                logger.warning(f"📱 [MOCK] Would send SMS to {recipient_phone} using template {template_name}")
                metadata = {"recipient": recipient_phone, "template": template_name, "mode": "mock"}
            else:
                # Real 2Factor R1 API call
                # Format: https://2factor.in/API/R1/?module=TRANS_SMS&apikey={api_key}&to={phone}&from={sender_id}&templatename={template_name}&var1={val1}&var2={val2}...
                
                params = {
                    "module": "TRANS_SMS",
                    "apikey": self.api_key,
                    "to": phone_number,
                    "from": self.sender_id,
                    "templatename": template_name
                }
                
                # Add variables (var1, var2, etc.) from data
                data = notification_data.get("data", {})
                
                # Mapping of templates to variables (as per images)
                if template_name == "BookingConfirm1":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("scheduled_at", "N/A")
                    params["var3"] = data.get("location_name", "Doffair Center")
                elif template_name == "BookingCancel":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("booking_id", "N/A")
                    params["var3"] = data.get("scheduled_at", "N/A")
                elif template_name == "BookingReschedule":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("booking_id", "N/A")
                    params["var3"] = data.get("postpone_date", "N/A")
                    params["var4"] = data.get("postpone_time", "N/A")
                    params["var5"] = data.get("vendor_name", "Doffair Vendor")
                elif template_name == "BookingStarted":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("service_name", "Service")
                    params["var3"] = data.get("booking_id", "N/A")
                elif template_name == "BookingCompleted":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("service_name", "Service")
                    params["var3"] = data.get("booking_id", "N/A")
                elif template_name == "WALKIN_BOOKING_CONFIRMED":
                    params["var1"] = data.get("user_name", "Customer")
                    params["var2"] = data.get("booking_date", "N/A")
                    params["var3"] = data.get("vendor_name", "Doffair Vendor")
                    params["var4"] = "https://doffair.com/download"
                else:
                    # Generic mapping for other templates (up to 5 vars)
                    for i in range(1, 6):
                        val = data.get(f"var{i}")
                        if val:
                            params[f"var{i}"] = val

                logger.info(f"📱 Attempting to send SMS to {recipient_phone} via 2Factor API")
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.api_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response_text = await response.text()
                        try:
                            response_data = await response.json()
                        except:
                            response_data = {"RawResponse": response_text}
                        
                        if response.status != 200 or response_data.get("Status") != "Success":
                            logger.error(f"❌ 2Factor API Error: {response_text}")
                            raise Exception(f"2Factor API error: {response_data}")
                        
                        logger.info(f"✅ SMS successfully sent to {recipient_phone}. Status: {response_data.get('Status')}, Details: {response_data.get('Details')}")
                        
                        metadata = {
                            "recipient": recipient_phone,
                            "template": template_name,
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
            error_msg = f"❌ Failed to send SMS to {recipient_phone if 'recipient_phone' in locals() else 'unknown'}: {str(e)}"
            logger.error(error_msg)
            self.log_failure(notification_data.get("notification_id"), error_msg)
            raise Exception(error_msg)
