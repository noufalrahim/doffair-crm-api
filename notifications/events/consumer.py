import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from notifications.events.schemas import EventPayload
from notifications.events.types import EventType, RecipientRole
from notifications.config.router import notification_router
from notifications.templates.renderer import template_renderer
from notifications.services.preferences_service import preferences_service
from notifications.services.idempotency_service import idempotency_service
from notifications.enums import NotificationChannel
from notifications.models.notification import NotificationLog, InAppNotification
from notifications.handlers.email_handler import EmailHandler
from notifications.handlers.sms_handler import SMSHandler
from notifications.handlers.whatsapp_handler import WhatsAppHandler
from notifications.services.pdf_service import pdf_service
from core.database import get_engine, get_secondary_engine
from core.enums import InvoiceStatus
from vendor.models.invoice import Invoice
from user.models.user import User
from odmantic import ObjectId

engine = get_engine()

logger = logging.getLogger(__name__)


def process_event(event_data: Dict[str, Any]):
    try:
        logger.info(f"📨 Processing event: {event_data.get('event_id')}")
        
        # Get or create event loop for this thread
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(process_event_async(event_data))
        # Don't close loop - RQ worker reuses it for multiple jobs
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process event: {str(e)}")
        raise


async def process_event_async(event_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        event = EventPayload(**event_data)
        
        logger.info(
            f"🔄 Processing event {event.event_id}: "
            f"{event.event_type} from {event.source}"
        )
        
        recipients = notification_router.get_recipients(event.event_type)
        
        if not recipients:
            logger.warning(f"⚠️ No recipients configured for event {event.event_type}")
            return {
                "event_id": event.event_id,
                "status": "no_recipients",
                "processed": 0
            }
        
        results = []
        for recipient_role in recipients:
            result = await process_recipient(event, recipient_role)
            results.extend(result)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        logger.info(
            f"✅ Event {event.event_id} processed: "
            f"{success_count}/{len(results)} notifications sent"
        )
        
        return {
            "event_id": event.event_id,
            "status": "completed",
            "processed": len(results),
            "successful": success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process event async: {str(e)}")
        raise


async def process_recipient(
    event: EventPayload,
    recipient_role: RecipientRole
) -> List[Dict[str, Any]]:
    try:
        role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
        recipient_id = extract_recipient_id(event.data, recipient_role)
        
        if not recipient_id:
            logger.warning(
                f"⚠️ Could not extract recipient ID for role {role_str} "
                f"from event {event.event_id}"
            )
            return []
        
        if not await preferences_service.is_event_enabled(recipient_id, event.event_type):
            logger.info(
                f"⏭️ Event {event.event_type} disabled for user {recipient_id}"
            )
            return []
        
        channels = notification_router.get_channels(event.event_type, recipient_role)
        channel_names = [c.value if hasattr(c, 'value') else str(c) for c in channels]
        logger.info(f"📤 Event {event.event_id} for role={role_str} recipient={recipient_id} → channels: {channel_names}")
        
        results = []
        for channel in channels:
            result = await send_notification(
                event, recipient_role, recipient_id, channel
            )
            results.append(result)
        
        return results
        
    except Exception as e:
        role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
        logger.error(
            f"❌ Failed to process recipient {role_str}: {str(e)}"
        )
        return []


async def send_notification(
    event: EventPayload,
    recipient_role: RecipientRole,
    recipient_id: str,
    channel: NotificationChannel
) -> Dict[str, Any]:
    try:
        if not await preferences_service.is_channel_enabled(recipient_id, channel):
            channel_str = channel.value if hasattr(channel, 'value') else str(channel)
            logger.info(
                f"⏭️ Channel {channel_str} disabled for user {recipient_id}"
            )
            return {
                "channel": channel_str,
                "success": False,
                "reason": "channel_disabled"
            }
        
        channel_str = channel.value if hasattr(channel, 'value') else str(channel)
        can_send = await idempotency_service.check_and_record(
            event.event_id, recipient_id, channel_str
        )
        
        if not can_send:
            logger.info(
                f"⏭️ Duplicate notification skipped: "
                f"event={event.event_id}, recipient={recipient_id}, channel={channel_str}"
            )
            return {
                "channel": channel_str,
                "success": False,
                "reason": "duplicate"
            }
        
        content = template_renderer.render(
            event.event_type, recipient_role, channel, event.data
        )
        
        if not content:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
            channel_str = channel.value if hasattr(channel, 'value') else str(channel)
            logger.warning(
                f"⚠️ No content rendered for {event_type_str}/{role_str}/{channel_str}"
            )
            return {
                "channel": channel_str,
                "success": False,
                "reason": "no_template"
            }
        
        if channel == NotificationChannel.IN_APP:
            success = await send_inapp_notification(
                event, recipient_id, recipient_role, content
            )
        elif channel == NotificationChannel.EMAIL:
            success = await send_email_notification(
                event, recipient_id, recipient_role, content
            )
        elif channel == NotificationChannel.SMS:
            success = await send_sms_notification(
                event, recipient_id, content
            )
        elif channel == NotificationChannel.WHATSAPP:
            success = await send_whatsapp_notification(
                event, recipient_id, content
            )
        else:
            success = False
        
        channel_str = channel.value if hasattr(channel, 'value') else str(channel)
        return {
            "channel": channel_str,
            "success": success,
            "recipient_id": recipient_id
        }
        
    except Exception as e:
        channel_str = channel.value if hasattr(channel, 'value') else str(channel)
        logger.error(
            f"❌ Failed to send notification via {channel_str}: {str(e)}"
        )
        return {
            "channel": channel_str,
            "success": False,
            "error": str(e)
        }


async def send_inapp_notification(
    event: EventPayload,
    recipient_id: str,
    recipient_role: RecipientRole,
    content: str
) -> bool:
    try:
        # Handle both enum and string event_type
        event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        recipient_role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
        
        notification = InAppNotification(
            user_id=recipient_id,
            title=get_notification_title(event.event_type),
            message=content,
            notification_type=event_type_str,
            metadata={
                "event_id": event.event_id,
                "recipient_role": recipient_role_str,
                **event.data
            }
        )
        
        await engine.save(notification)
        logger.info(f"✅ In-app notification created for user {recipient_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create in-app notification: {str(e)}")
        return False


async def send_email_notification(
    event: EventPayload,
    recipient_id: str,
    recipient_role: RecipientRole,
    content: str
) -> bool:
    try:
        email = extract_email(event.data, recipient_role)
        print(f"[EMAIL] Extracted email for {recipient_id}: '{email}'")
        
        # Fallback: if email is empty, try fetching from DB using user_id/customer_id
        if not email:
            fallback_uid = event.data.get("user_id") or event.data.get("customer_id")
            if fallback_uid:
                print(f"[EMAIL] ⚠️ Empty email — DB lookup for user_id={fallback_uid}")
                try:
                    # Users live in secondary DB (doffair_dev)
                    sec_engine = get_secondary_engine()
                    user_col = sec_engine.database.get_collection("users")
                    raw = await user_col.find_one({"_id": ObjectId(fallback_uid)})
                    if raw and raw.get("email"):
                        email = raw["email"]
                        print(f"[EMAIL] ✅ DB fallback found email: '{email}'")
                    else:
                        print(f"[EMAIL] ❌ DB fallback: user not found or email empty for id={fallback_uid}. Raw={raw}")
                except Exception as db_err:
                    print(f"[EMAIL] ❌ DB fallback error: {db_err}")
        
        if not email:
            print(f"[EMAIL] ⚠️ No email found for recipient {recipient_id}. Data keys: {list(event.data.keys())}")
            logger.warning(f"⚠️ No email found for recipient {recipient_id}")
            return False
        
        print(f"[EMAIL] 📧 Sending email to: {email} | Subject: {get_notification_title(event.event_type)}")
        handler = EmailHandler()
        notification_data = {
            "recipient_email": email,
            "subject": get_notification_title(event.event_type),
            "message": content,
            "notification_id": event.event_id,
            "template_id": event.data.get("template_id"),
            "data": event.data
        }

        # Handle Invoice PDF Attachment
        if event.event_type == EventType.INVOICE_SENT:
            invoice_id = event.data.get("invoice_id")
            if invoice_id:
                try:
                    invoice = await engine.find_one(Invoice, Invoice.id == ObjectId(invoice_id))
                    if invoice:
                        invoice_dict = invoice.model_dump()
                        pdf_content = pdf_service.generate_invoice_pdf(invoice_dict)
                        
                        if pdf_content:
                            if "attachments" not in notification_data:
                                notification_data["attachments"] = []
                            
                            notification_data["attachments"].append({
                                "filename": f"Invoice_{invoice.invoice_number}.pdf",
                                "content": pdf_content
                            })
                            logger.info(f"📎 Attached PDF for invoice {invoice.invoice_number}")
                except Exception as ex:
                    logger.error(f"❌ Failed to attach PDF to email: {str(ex)}")

        result = await handler.send(notification_data)
        success = result.get("success", False)
        if success:
            print(f"[EMAIL] ✅ Email sent successfully to {email}")
        else:
            print(f"[EMAIL] ❌ Email send returned failure for {email}")
        return success
        
    except Exception as e:
        print(f"[EMAIL] ❌ Exception while sending email: {str(e)}")
        logger.error(f"❌ Failed to send email: {str(e)}")
        import traceback; traceback.print_exc()
        return False


async def send_sms_notification(
    event: EventPayload,
    recipient_id: str,
    content: str
) -> bool:
    try:
        phone = extract_phone(event.data)
        print(f"[SMS] Extracted phone for {recipient_id}: '{phone}'")
        if not phone:
            print(f"[SMS] ⚠️ No phone found in event data for recipient {recipient_id}. Data keys: {list(event.data.keys())}")
            logger.warning(f"⚠️ No phone found for recipient {recipient_id}")
            return False
        
        print(f"[SMS] 📱 Sending SMS to: {phone} | Template: {event.data.get('template_id')}")
        handler = SMSHandler()
        notification_data = {
            "recipient_phone": phone,
            "message": content,
            "notification_id": event.event_id,
            "template_id": event.data.get("template_id"),
            "data": event.data
        }
        result = await handler.send(notification_data)
        success = result.get("success", False)
        if success:
            print(f"[SMS] ✅ SMS sent successfully to {phone}")
        else:
            print(f"[SMS] ❌ SMS send returned failure for {phone}")
        return success
        
    except Exception as e:
        print(f"[SMS] ❌ Exception while sending SMS: {str(e)}")
        logger.error(f"❌ Failed to send SMS: {str(e)}")
        import traceback; traceback.print_exc()
        return False


async def send_whatsapp_notification(
    event: EventPayload,
    recipient_id: str,
    content: str
) -> bool:
    try:
        phone = extract_phone(event.data)
        if not phone:
            logger.warning(f"⚠️ No phone found for recipient {recipient_id}")
            return False
        
        handler = WhatsAppHandler()
        notification_data = {
            "recipient_whatsapp": phone,
            "body": content,
            "notification_id": event.event_id,
            "data": event.data
        }
        result = await handler.send(notification_data)
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ Failed to send WhatsApp: {str(e)}")
        return False


def extract_recipient_id(data: Dict[str, Any], role: RecipientRole) -> str:
    # Handle both enum and string
    role_str = role.value if hasattr(role, 'value') else str(role)
    
    if role_str == "user" or role == RecipientRole.USER:
        return data.get("user_id", "")
    elif role_str == "vendor" or role == RecipientRole.VENDOR:
        return data.get("vendor_id", "")
    elif role_str == "admin" or role == RecipientRole.ADMIN:
        return data.get("admin_id", "")
    return ""


def extract_email(data: Dict[str, Any], role: RecipientRole) -> str:
    # Handle both enum and string
    role_str = role.value if hasattr(role, 'value') else str(role)
    
    if role_str == "user" or role == RecipientRole.USER:
        return data.get("user_email", "")
    elif role_str == "vendor" or role == RecipientRole.VENDOR:
        return data.get("vendor_email", "")
    return ""


def extract_phone(data: Dict[str, Any]) -> str:
    return data.get("user_phone") or data.get("vendor_phone") or ""


def get_notification_title(event_type: EventType) -> str:
    # Handle both enum and string
    event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
    
    titles = {
        "BOOKING_CREATED": "Booking Confirmed",
        "BOOKING_CANCELLED": "Booking Cancelled",
        "BOOKING_RESCHEDULED": "Booking Rescheduled",
        "BOOKING_CONFIRMED": "Booking Confirmed by Vendor",
        "BOOKING_COMPLETED": "Service Completed",
        "BOOKING_STARTED": "Service Started",
        "PAYMENT_SUCCESS": "Payment Successful",
        "PAYMENT_FAILED": "Payment Failed",
        "PAYMENT_REFUNDED": "Payment Refunded",
        "USER_REGISTERED": "Welcome to Doffair",
        "USER_VERIFIED": "Account Verified",
        "PASSWORD_RESET_REQUESTED": "Password Reset Request",
        "VENDOR_APPROVED": "Vendor Application Approved",
        "VENDOR_REJECTED": "Vendor Application Update"
    }
    return titles.get(event_type_str, event_type_str.replace("_", " ").title())
