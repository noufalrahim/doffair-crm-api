"""
Reminder Service - Business logic for custom vendor reminders
Integrates with notification system to send scheduled reminders
"""
import logging
from datetime import datetime
from odmantic import AIOEngine
from typing import Optional, List
from vendor.models.reminder import Reminder
from user.models.booking import Booking
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource

logger = logging.getLogger(__name__)


async def create_reminder(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: str,
    title: str,
    message: str,
    reminder_type: str,
    scheduled_at: datetime,
    send_sms: bool = True,
    send_email: bool = False,
    send_whatsapp: bool = False,
    send_in_app: bool = True,
    notes: str = ""
) -> Reminder:
    """
    Create a new reminder for a customer
    Links to booking and extracts customer information
    """
    try:
        # Get booking to extract customer info
        booking = await engine.find_one(
            Booking,
            (Booking.id == booking_id) & (Booking.vendor_id == vendor_id)
        )
        
        if not booking:
            raise ValueError(f"Booking {booking_id} not found or does not belong to vendor")
        
        logger.info(f"Creating reminder for booking {booking_id}, customer: {booking.user_phone}")
        
        # Create reminder
        reminder = Reminder(
            vendor_id=vendor_id,
            customer_id=booking.user_id,
            booking_id=booking_id,
            title=title,
            message=message,
            reminder_type=reminder_type,
            scheduled_at=scheduled_at,
            send_sms=send_sms,
            send_email=send_email,
            send_whatsapp=send_whatsapp,
            send_in_app=send_in_app,
            notes=notes or "",
            status="PENDING",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await engine.save(reminder)
        logger.info(f"✅ Reminder created: {reminder.id} for {booking.user_phone}")
        
        return reminder
        
    except ValueError as e:
        logger.error(f"Validation error creating reminder: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to create reminder: {str(e)}")
        raise Exception(f"Failed to create reminder: {str(e)}")


async def get_reminder(
    engine: AIOEngine,
    vendor_id: str,
    reminder_id: str
) -> Optional[Reminder]:
    """Get single reminder by ID"""
    try:
        reminder = await engine.find_one(
            Reminder,
            (Reminder.id == reminder_id) & (Reminder.vendor_id == vendor_id)
        )
        
        if not reminder:
            logger.warning(f"Reminder {reminder_id} not found for vendor {vendor_id}")
            return None
        
        return reminder
        
    except Exception as e:
        logger.error(f"Failed to get reminder {reminder_id}: {str(e)}")
        raise


async def list_reminders(
    engine: AIOEngine,
    vendor_id: str,
    booking_id: Optional[str] = None,
    customer_phone: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Reminder]:
    """
    List reminders with filtering
    Can filter by booking_id, customer_phone, or status
    """
    try:
        # Build query
        query = (Reminder.vendor_id == vendor_id) & (Reminder.is_active == True)
        
        if booking_id:
            query &= (Reminder.booking_id == booking_id)
        
        if status:
            query &= (Reminder.status == status)
        
        if customer_phone:
            # Get all bookings for this customer
            bookings = await engine.find(
                Booking,
                (Booking.vendor_id == vendor_id) & (Booking.user_phone == customer_phone)
            )
            booking_ids = [str(b.id) for b in bookings]
            
            if not booking_ids:
                return []
            
            query &= (Reminder.booking_id.in_(booking_ids)) & (Reminder.booking_id != "")
        
        # Execute query
        reminders = await engine.find(
            Reminder,
            query,
            sort=Reminder.scheduled_at.desc(),
            skip=skip,
            limit=limit
        )
        
        return list(reminders)
        
    except Exception as e:
        logger.error(f"Failed to list reminders: {str(e)}")
        raise


async def update_reminder(
    engine: AIOEngine,
    vendor_id: str,
    reminder_id: str,
    **update_data
) -> Optional[Reminder]:
    """Update reminder fields"""
    try:
        reminder = await get_reminder(engine, vendor_id, reminder_id)
        
        if not reminder:
            return None
        
        # Only allow updating if status is PENDING
        if reminder.status != "PENDING":
            raise ValueError(f"Cannot update reminder with status {reminder.status}")
        
        # Update allowed fields
        for field, value in update_data.items():
            if value is not None and hasattr(reminder, field):
                setattr(reminder, field, value)
        
        reminder.updated_at = datetime.utcnow()
        
        await engine.save(reminder)
        logger.info(f"✅ Reminder updated: {reminder_id}")
        
        return reminder
        
    except ValueError as e:
        logger.error(f"Validation error updating reminder: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to update reminder {reminder_id}: {str(e)}")
        raise


async def delete_reminder(
    engine: AIOEngine,
    vendor_id: str,
    reminder_id: str
) -> bool:
    """Soft delete reminder (mark as inactive)"""
    try:
        reminder = await get_reminder(engine, vendor_id, reminder_id)
        
        if not reminder:
            return False
        
        # Only allow deletion if not sent
        if reminder.status == "SENT":
            raise ValueError("Cannot delete reminder that has already been sent")
        
        reminder.is_active = False
        reminder.updated_at = datetime.utcnow()
        
        await engine.save(reminder)
        logger.info(f"✅ Reminder deleted: {reminder_id}")
        
        return True
        
    except ValueError as e:
        logger.error(f"Validation error deleting reminder: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to delete reminder {reminder_id}: {str(e)}")
        raise


async def send_reminder_now(
    engine: AIOEngine,
    vendor_id: str,
    reminder_id: str
) -> bool:
    """
    Manually trigger a reminder to be sent immediately
    Publishes event to notification system
    """
    try:
        reminder = await get_reminder(engine, vendor_id, reminder_id)
        
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found")
        
        if reminder.status != "PENDING":
            raise ValueError(f"Reminder already {reminder.status}")
        
        # Get booking for customer details
        booking = await engine.find_one(Booking, Booking.id == reminder.booking_id)
        
        if not booking:
            raise ValueError(f"Booking {reminder.booking_id} not found")
        
        logger.info(f"Sending reminder {reminder_id} to {booking.user_phone}")
        
        # Build notification channels
        channels = []
        if reminder.send_sms:
            channels.append("sms")
        if reminder.send_email:
            channels.append("email")
        if reminder.send_whatsapp:
            channels.append("whatsapp")
        if reminder.send_in_app:
            channels.append("in_app")
        
        # Publish event to notification system
        event_publisher.publish(
            event_type=EventType.CUSTOM_REMINDER,
            data={
                "reminder_id": str(reminder.id),
                "booking_id": reminder.booking_id,
                "customer_id": reminder.customer_id,
                "customer_name": booking.user_name,
                "customer_phone": booking.user_phone,
                "customer_email": booking.user_email,
                "title": reminder.title,
                "message": reminder.message,
                "reminder_type": reminder.reminder_type,
                "channels": channels,
                "scheduled_at": reminder.scheduled_at.isoformat()
            },
            source=EventSource.VENDOR_SERVICE
        )
        
        # Update reminder status
        reminder.status = "SENT"
        reminder.sent_at = datetime.utcnow()
        reminder.updated_at = datetime.utcnow()
        
        await engine.save(reminder)
        logger.info(f"✅ Reminder sent: {reminder_id}")
        
        return True
        
    except ValueError as e:
        logger.error(f"Validation error sending reminder: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to send reminder {reminder_id}: {str(e)}")
        raise


async def process_scheduled_reminders(engine: AIOEngine) -> int:
    """
    Process all pending reminders that are due to be sent
    Should be called by a cron job or background worker
    Returns count of reminders processed
    """
    try:
        # Find all pending reminders scheduled for now or earlier
        now = datetime.utcnow()
        
        due_reminders = await engine.find(
            Reminder,
            (Reminder.status == "PENDING") &
            (Reminder.is_active == True) &
            (Reminder.scheduled_at <= now)
        )
        
        count = 0
        for reminder in due_reminders:
            try:
                await send_reminder_now(engine, reminder.vendor_id, str(reminder.id))
                count += 1
            except Exception as e:
                logger.error(f"Failed to send scheduled reminder {reminder.id}: {str(e)}")
                # Mark as failed
                reminder.status = "FAILED"
                reminder.error_message = str(e)[:500]
                reminder.updated_at = datetime.utcnow()
                await engine.save(reminder)
        
        if count > 0:
            logger.info(f"✅ Processed {count} scheduled reminders")
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to process scheduled reminders: {str(e)}")
        raise
