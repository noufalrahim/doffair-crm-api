import json
import asyncio
import logging
from redis import Redis
from core.config import settings
from notifications.handlers.email_handler import EmailHandler
from notifications.handlers.sms_handler import SMSHandler
from notifications.services.pdf_service import pdf_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimpleNotificationWorker")

# Redis configuration
REDIS_QUEUE_NAME = "doffair:notifications_queue"

async def process_job(payload_str):
    try:
        data = json.loads(payload_str)
        logger.info(f"📥 Received job: {payload_str[:200]}...")
        
        # --- Handle Python EventPayload format ---
        if "event_type" in data and "data" in data:
            event_type = data.get("event_type")
            event_data = data.get("data")
            logger.info(f"🎭 Processing Python Event: {event_type}")
            
            # Map variables list to var1, var2... if present
            vars_input = event_data.get("variables")
            if isinstance(vars_input, list):
                event_data.update({f"var{i+1}": val for i, val in enumerate(vars_input)})
            
            # --- Special Handling for OTP (Fallback logic: Email if SMS fails) ---
            if event_type == "SERVICE_START_OTP" or event_data.get("template_id") == "SERVICE_START_OTP":
                logger.info(f"🔐 Handling OTP with fallback logic (SMS -> Email) for event: {event_type}")
                sms_success = False
                
                # 1. Try SMS
                if event_data.get("user_phone"):
                    try:
                        handler = SMSHandler()
                        notif = {
                            "recipient_phone": event_data["user_phone"],
                            "template_id": "SERVICE_START_OTP",
                            "data": event_data
                        }
                        logger.info(f"📱 Attempting OTP SMS to {event_data['user_phone']}")
                        await handler.send(notif)
                        sms_success = True
                    except Exception as e:
                        logger.error(f"❌ OTP SMS failed: {str(e)}. Falling back to Email.")
                
                # 2. Try Email if SMS failed or was not possible
                if not sms_success and event_data.get("user_email"):
                    try:
                        handler = EmailHandler()
                        notif = {
                            "recipient_email": event_data["user_email"],
                            "template_id": "SERVICE_START_OTP",
                            "subject": "Your Doffair Verification Code",
                            "message": event_data.get("message", "Your OTP is being sent."),
                            "data": event_data
                        }
                        logger.info(f"📧 Attempting OTP Email to {event_data['user_email']}")
                        await handler.send(notif)
                    except Exception as e:
                        logger.error(f"❌ OTP Email also failed: {str(e)}")
                
                return

            # --- Special Handling for Invoices (PDF Generation) ---
            if event_type == "INVOICE_SENT":
                logger.info(f"📄 Handling Invoice with PDF generation for: {event_data.get('invoice_number')}")
                pdf_content = pdf_service.generate_invoice_pdf(event_data)
                if pdf_content:
                    event_data["attachments"] = [{
                        "filename": f"Invoice_{event_data.get('invoice_number')}.pdf",
                        "content": pdf_content
                    }]
                    logger.info(f"✅ PDF generated and attached for invoice {event_data.get('invoice_number')}")
                else:
                    logger.warning(f"⚠️ PDF generation failed for invoice {event_data.get('invoice_number')}")

            # --- Standard Handling for other events (Send both) ---
            # 1. Email
            if event_data.get("user_email") or event_data.get("vendor_email"):
                handler = EmailHandler()
                recipients = []
                if event_data.get("user_email"): recipients.append(event_data["user_email"])
                if event_data.get("vendor_email"): recipients.append(event_data["vendor_email"])
                
                for email in recipients:
                    notif = {
                        "recipient_email": email,
                        "template_id": event_data.get("template_id") or event_type,
                        "subject": f"Doffair Alert: {event_type}",
                        "data": event_data,
                        "attachments": event_data.get("attachments", [])
                    }
                    logger.info(f"📧 Dispatching Email to {email}")
                    try:
                        await handler.send(notif)
                    except Exception as e:
                        logger.error(f"❌ Email dispatch failed for {email}: {e}")
            
            # 2. SMS
            if event_data.get("user_phone") or event_data.get("vendor_phone"):
                handler = SMSHandler()
                phones = []
                if event_data.get("user_phone"): phones.append(event_data["user_phone"])
                if event_data.get("vendor_phone"): phones.append(event_data["vendor_phone"])
                
                for phone in phones:
                    notif = {
                        "recipient_phone": phone,
                        "template_id": event_data.get("template_id") or event_type,
                        "data": event_data
                    }
                    logger.info(f"📱 Dispatching SMS to {phone}")
                    try:
                        await handler.send(notif)
                    except Exception as e:
                        logger.error(f"❌ SMS dispatch failed for {phone}: {e}")
            
            return

        # --- Handle Java / Simple format ---
        is_email = bool(data.get("toEmail"))
        is_sms = bool(data.get("phoneNumber"))
        
        if is_email:
            handler = EmailHandler()
            notification_data = {
                "recipient_email": data.get("toEmail"),
                "subject": data.get("subject", "Doffair Notification"),
                "message": data.get("content", ""),
                "template_id": data.get("templateName"),
                "data": data.get("variables", {}) if isinstance(data.get("variables"), dict) else {}
            }
            
            # If variables is a list (from Java), map it to var1, var2...
            if isinstance(data.get("variables"), list):
                notification_data["data"] = {f"var{i+1}": val for i, val in enumerate(data.get("variables"))}
            
            logger.info(f"📧 Processing Email to: {notification_data['recipient_email']}")
            await handler.send(notification_data)
            
        if is_sms:
            handler = SMSHandler()
            notification_data = {
                "recipient_phone": data.get("phoneNumber"),
                "template_id": data.get("templateName"),
                "data": {}
            }
            
            # Map variables list to var1, var2... for 2Factor API
            vars_input = data.get("variables")
            if isinstance(vars_input, list):
                notification_data["data"] = {f"var{i+1}": val for i, val in enumerate(vars_input)}
                # Also add specific mappings often used in SMSHandler
                if vars_input:
                    notification_data["data"]["user_name"] = vars_input[0]
                if len(vars_input) > 1:
                    notification_data["data"]["scheduled_at"] = vars_input[1]
                if len(vars_input) > 2:
                    notification_data["data"]["location_name"] = vars_input[2]
            elif isinstance(vars_input, dict):
                notification_data["data"] = vars_input

            logger.info(f"📱 Processing SMS to: {notification_data['recipient_phone']} [Template: {notification_data['template_id']}]")
            await handler.send(notification_data)

        if not is_email and not is_sms:
            logger.warning("⚠️ Received job with neither email nor phone number. Skipping.")

    except Exception as e:
        logger.error(f"❌ Failed to process job: {str(e)}")

async def worker():
    logger.info("=" * 60)
    logger.info("🚀 Starting Simple Notification Worker (Redis List version)")
    logger.info(f"📡 Redis URL: {settings.REDIS_URL}")
    logger.info(f"📋 Listening on: {REDIS_QUEUE_NAME}")
    logger.info("=" * 60)
    
    # Initialize Redis connection
    try:
        redis_conn = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_conn.ping()
        logger.info("✅ Connected to Redis successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {str(e)}")
        return

    while True:
        try:
            # BRPOP blocks until an item is available in the list
            # Returns (queue_name, item)
            result = redis_conn.brpop(REDIS_QUEUE_NAME, timeout=30)
            
            if result:
                _, payload_str = result
                await process_job(payload_str)
            
        except KeyboardInterrupt:
            logger.info("⏸️ Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"⚠️ Worker loop error: {str(e)}")
            await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    try:
        asyncio.run(worker())
    except KeyboardInterrupt:
        pass
