from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource
from notifications.events.schemas import (
    BookingEventData,
    PaymentEventData,
    UserEventData,
    VendorEventData
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


class PublishEventRequest(BaseModel):
    event_type: EventType
    source: EventSource
    data: Dict[str, Any]
    event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PublishEventResponse(BaseModel):
    success: bool
    event_id: str
    message: str


class PublishBookingEventRequest(BaseModel):
    event_type: EventType
    source: EventSource = EventSource.BOOKING_SERVICE
    data: BookingEventData
    event_id: Optional[str] = None


class PublishPaymentEventRequest(BaseModel):
    event_type: EventType
    source: EventSource = EventSource.PAYMENT_SERVICE
    data: PaymentEventData
    event_id: Optional[str] = None


@router.post("/publish", response_model=PublishEventResponse)
async def publish_event(request: PublishEventRequest):
    try:
        logger.info(f"📤 Publishing event: {request.event_type.value}")
        
        event_id = event_publisher.publish(
            event_type=request.event_type,
            data=request.data,
            source=request.source,
            event_id=request.event_id,
            metadata=request.metadata
        )
        
        return PublishEventResponse(
            success=True,
            event_id=event_id,
            message=f"Event {request.event_type.value} published successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to publish event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish event: {str(e)}"
        )


@router.post("/publish/booking", response_model=PublishEventResponse)
async def publish_booking_event(request: PublishBookingEventRequest):
    try:
        logger.info(f"📤 Publishing booking event: {request.event_type.value}")
        
        event_id = event_publisher.publish(
            event_type=request.event_type,
            data=request.data.model_dump(mode='json'),
            source=request.source,
            event_id=request.event_id
        )
        
        return PublishEventResponse(
            success=True,
            event_id=event_id,
            message=f"Booking event {request.event_type.value} published successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to publish booking event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish booking event: {str(e)}"
        )


@router.post("/publish/payment", response_model=PublishEventResponse)
async def publish_payment_event(request: PublishPaymentEventRequest):
    try:
        logger.info(f"📤 Publishing payment event: {request.event_type.value}")
        
        event_id = event_publisher.publish(
            event_type=request.event_type,
            data=request.data.model_dump(mode='json'),
            source=request.source,
            event_id=request.event_id
        )
        
        return PublishEventResponse(
            success=True,
            event_id=event_id,
            message=f"Payment event {request.event_type.value} published successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to publish payment event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish payment event: {str(e)}"
        )


@router.get("/queue/info")
async def get_queue_info():
    try:
        info = event_publisher.get_queue_info()
        return info
    except Exception as e:
        logger.error(f"❌ Failed to get queue info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue info: {str(e)}"
        )
