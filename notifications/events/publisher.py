import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from redis import Redis
from rq import Queue
from notifications.events.schemas import EventPayload
from notifications.events.types import EventType, EventSource
from core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self):
        self._redis_conn: Optional[Redis] = None
        self._queue: Optional[Queue] = None
        # Don't connect immediately - lazy connection
    
    def _ensure_connection(self):
        """Ensure Redis connection is established before use"""
        if self._redis_conn is None:
            self._connect()
    
    def _connect(self):
        """Connect to Redis with retry logic and increased timeouts for Docker"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
                self._redis_conn = Redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=10,  # Increased for Docker
                    socket_timeout=10,  # Increased for Docker
                    socket_keepalive=True,
                    health_check_interval=30
                )
                
                self._redis_conn.ping()
                
                queue_name = getattr(settings, "REDIS_QUEUE_NAME", "doffair:notifications")
                self._queue = Queue(queue_name, connection=self._redis_conn)
                
                logger.info(f"✅ Event publisher connected to Redis: {redis_url}")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Event publisher Redis connection attempt {attempt + 1} failed: {str(e)}")
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    # Don't crash the server - allow it to start without Redis
                    logger.error(f"❌ Failed to connect Event Publisher to Redis after {max_retries} attempts: {str(e)}")
                    logger.error("💡 Make sure Redis/Docker is running: docker ps | grep redis")
                    logger.warning("⚠️ Server will start but event publishing will be unavailable")
                    # Don't raise - just leave _redis_conn as None
                    return
    
    def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: EventSource,
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        # Ensure connection is established
        self._ensure_connection()
        
        # If Redis is not available, log warning and return placeholder event_id
        if self._redis_conn is None or self._queue is None:
            logger.warning(f"⚠️ Cannot publish event {event_type} - Redis not connected")
            # Return event_id so caller doesn't crash, but event won't be processed
            generated_event_id = event_id or f"evt_{int(datetime.utcnow().timestamp() * 1000)}"
            logger.error(f"❌ Event {generated_event_id} NOT published - notification service unavailable")
            return generated_event_id
        
        try:
            # Generate event ID as string to avoid serialization issues
            generated_event_id = event_id or f"evt_{int(datetime.utcnow().timestamp() * 1000)}"
            
            event_payload = EventPayload(
                event_id=generated_event_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                source=source,
                data=data,
                metadata=metadata or {}
            )
            
            # Serialize to JSON string then parse to dict - this ensures datetime objects are ISO strings
            payload_json_str = event_payload.model_dump_json()
            payload_dict = json.loads(payload_json_str)
            
            job = self._queue.enqueue(
                'notifications.events.consumer.process_event',
                payload_dict,
                job_timeout=None,
                retry=None,
                result_ttl=500
            )
            
            logger.info(
                f"📤 Event published: {event_type.value} | "
                f"Event ID: {generated_event_id} | "
                f"Job ID: {job.id}"
            )
            
            return generated_event_id
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event_type.value}: {str(e)}")
            raise
    
    def get_queue_info(self) -> Dict[str, Any]:
        try:
            if not self._queue:
                return {"error": "Queue not initialized"}
            
            return {
                "queue_name": self._queue.name,
                "pending_jobs": len(self._queue),
                "redis_connected": self._redis_conn.ping() if self._redis_conn else False
            }
        except Exception as e:
            logger.error(f"❌ Failed to get queue info: {str(e)}")
            return {"error": str(e)}


event_publisher = EventPublisher()
