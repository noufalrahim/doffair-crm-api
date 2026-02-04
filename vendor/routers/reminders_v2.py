"""
Reminder Router - API endpoints for custom vendor reminders
Allows vendors to create and manage follow-up reminders
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from core.security import get_current_vendor
from core.database import get_engine
from vendor.schemas.reminder_v2 import (
    CreateReminderRequest,
    ReminderResponse,
    ReminderListResponse,
    UpdateReminderRequest
)
from vendor.services import reminder_service_v2 as reminder_service
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vendor/reminders",
    tags=["Vendor Reminders"]
)


@router.post("", response_model=dict)
async def create_reminder(
    request: CreateReminderRequest,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    Create a new reminder for a customer
    
    - Links to a booking_id
    - Automatically extracts customer info from booking
    - Schedules notification to be sent at specified time
    - Supports multiple channels: SMS, Email, WhatsApp, In-App
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        reminder = await reminder_service.create_reminder(
            engine=engine,
            vendor_id=vendor_id,
            booking_id=request.booking_id,
            title=request.title,
            message=request.message,
            reminder_type=request.reminder_type,
            scheduled_at=request.scheduled_at,
            send_sms=request.send_sms,
            send_email=request.send_email,
            send_whatsapp=request.send_whatsapp,
            send_in_app=request.send_in_app,
            notes=request.notes or ""
        )
        
        response_data = ReminderResponse(
            id=str(reminder.id),
            vendor_id=reminder.vendor_id,
            customer_id=reminder.customer_id,
            booking_id=reminder.booking_id,
            title=reminder.title,
            message=reminder.message,
            reminder_type=reminder.reminder_type,
            send_sms=reminder.send_sms,
            send_email=reminder.send_email,
            send_whatsapp=reminder.send_whatsapp,
            send_in_app=reminder.send_in_app,
            status=reminder.status,
            error_message=reminder.error_message,
            sms_status=reminder.sms_status,
            email_status=reminder.email_status,
            whatsapp_status=reminder.whatsapp_status,
            notes=reminder.notes,
            is_active=reminder.is_active,
            scheduled_at=reminder.scheduled_at,
            sent_at=reminder.sent_at,
            created_at=reminder.created_at,
            updated_at=reminder.updated_at
        )
        
        return success_response(
            data=response_data.model_dump(),
            message="Reminder created successfully"
        ).model_dump()
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"Failed to create reminder: {str(e)}")
        return error_response(
            message=f"Failed to create reminder: {str(e)}"
        ).model_dump()


@router.get("/{reminder_id}", response_model=dict)
async def get_reminder(
    reminder_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    Get single reminder by ID
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        reminder = await reminder_service.get_reminder(
            engine=engine,
            vendor_id=vendor_id,
            reminder_id=reminder_id
        )
        
        if not reminder:
            return error_response(
                message=f"Reminder {reminder_id} not found"
            ).model_dump()
        
        response_data = ReminderResponse(
            id=str(reminder.id),
            vendor_id=reminder.vendor_id,
            customer_id=reminder.customer_id,
            booking_id=reminder.booking_id,
            title=reminder.title,
            message=reminder.message,
            reminder_type=reminder.reminder_type,
            send_sms=reminder.send_sms,
            send_email=reminder.send_email,
            send_whatsapp=reminder.send_whatsapp,
            send_in_app=reminder.send_in_app,
            status=reminder.status,
            error_message=reminder.error_message,
            sms_status=reminder.sms_status,
            email_status=reminder.email_status,
            whatsapp_status=reminder.whatsapp_status,
            notes=reminder.notes,
            is_active=reminder.is_active,
            scheduled_at=reminder.scheduled_at,
            sent_at=reminder.sent_at,
            created_at=reminder.created_at,
            updated_at=reminder.updated_at
        )
        
        return success_response(data=response_data.model_dump()).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to get reminder: {str(e)}")
        return error_response(
            message=f"Failed to get reminder: {str(e)}"
        ).model_dump()


@router.get("", response_model=dict)
async def list_reminders(
    booking_id: Optional[str] = Query(None, description="Filter by booking ID"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SENT, FAILED)"),
    skip: int = Query(0, ge=0, description="Skip N reminders"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    List reminders with optional filters
    
    - Filter by booking_id: Get all reminders for a specific booking
    - Filter by customer_phone: Get all reminders for a customer across all bookings
    - Filter by status: PENDING, SENT, FAILED
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        reminders = await reminder_service.list_reminders(
            engine=engine,
            vendor_id=vendor_id,
            booking_id=booking_id,
            customer_phone=customer_phone,
            status=status,
            skip=skip,
            limit=limit
        )
        
        reminder_list = [
            ReminderResponse(
                id=str(r.id),
                vendor_id=r.vendor_id,
                customer_id=r.customer_id,
                booking_id=r.booking_id,
                title=r.title,
                message=r.message,
                reminder_type=r.reminder_type,
                send_sms=r.send_sms,
                send_email=r.send_email,
                send_whatsapp=r.send_whatsapp,
                send_in_app=r.send_in_app,
                status=r.status,
                error_message=r.error_message,
                sms_status=r.sms_status,
                email_status=r.email_status,
                whatsapp_status=r.whatsapp_status,
                notes=r.notes,
                is_active=r.is_active,
                scheduled_at=r.scheduled_at,
                sent_at=r.sent_at,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            for r in reminders
        ]
        
        response_data = ReminderListResponse(
            total=len(reminder_list),
            reminders=reminder_list
        )
        
        return success_response(data=response_data.model_dump()).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to list reminders: {str(e)}")
        return error_response(
            message=f"Failed to list reminders: {str(e)}"
        ).model_dump()


@router.patch("/{reminder_id}", response_model=dict)
async def update_reminder(
    reminder_id: str,
    request: UpdateReminderRequest,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    Update reminder details
    
    - Can only update PENDING reminders
    - Cannot update reminders that have already been sent
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        # Build update dict with only provided fields
        update_data = {
            k: v for k, v in request.model_dump().items()
            if v is not None
        }
        
        if not update_data:
            return error_response(
                message="No fields to update"
            ).model_dump()
        
        reminder = await reminder_service.update_reminder(
            engine=engine,
            vendor_id=vendor_id,
            reminder_id=reminder_id,
            **update_data
        )
        
        if not reminder:
            return error_response(
                message=f"Reminder {reminder_id} not found"
            ).model_dump()
        
        response_data = ReminderResponse(
            id=str(reminder.id),
            vendor_id=reminder.vendor_id,
            customer_id=reminder.customer_id,
            booking_id=reminder.booking_id,
            title=reminder.title,
            message=reminder.message,
            reminder_type=reminder.reminder_type,
            send_sms=reminder.send_sms,
            send_email=reminder.send_email,
            send_whatsapp=reminder.send_whatsapp,
            send_in_app=reminder.send_in_app,
            status=reminder.status,
            error_message=reminder.error_message,
            sms_status=reminder.sms_status,
            email_status=reminder.email_status,
            whatsapp_status=reminder.whatsapp_status,
            notes=reminder.notes,
            is_active=reminder.is_active,
            scheduled_at=reminder.scheduled_at,
            sent_at=reminder.sent_at,
            created_at=reminder.created_at,
            updated_at=reminder.updated_at
        )
        
        return success_response(
            data=response_data.model_dump(),
            message="Reminder updated successfully"
        ).model_dump()
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"Failed to update reminder: {str(e)}")
        return error_response(
            message=f"Failed to update reminder: {str(e)}"
        ).model_dump()


@router.delete("/{reminder_id}", response_model=dict)
async def delete_reminder(
    reminder_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    Delete (soft delete) a reminder
    
    - Cannot delete reminders that have already been sent
    - Marks reminder as inactive
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        success = await reminder_service.delete_reminder(
            engine=engine,
            vendor_id=vendor_id,
            reminder_id=reminder_id
        )
        
        if not success:
            return error_response(
                message=f"Reminder {reminder_id} not found"
            ).model_dump()
        
        return success_response(
            message="Reminder deleted successfully"
        ).model_dump()
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"Failed to delete reminder: {str(e)}")
        return error_response(
            message=f"Failed to delete reminder: {str(e)}"
        ).model_dump()


@router.post("/{reminder_id}/send", response_model=dict)
async def send_reminder_now(
    reminder_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """
    Manually trigger a reminder to be sent immediately
    
    - Overrides scheduled_at time
    - Sends notification via configured channels
    - Updates reminder status to SENT
    """
    try:
        vendor_id = current_vendor["vendor_id"]
        
        success = await reminder_service.send_reminder_now(
            engine=engine,
            vendor_id=vendor_id,
            reminder_id=reminder_id
        )
        
        return success_response(
            message="Reminder sent successfully"
        ).model_dump()
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(message=str(e)).model_dump()
    except Exception as e:
        logger.error(f"Failed to send reminder: {str(e)}")
        return error_response(
            message=f"Failed to send reminder: {str(e)}"
        ).model_dump()
