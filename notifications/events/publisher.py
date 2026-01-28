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
        self._connect()
    
    def _connect(self):
        try:
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            self._redis_conn = Redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            self._redis_conn.ping()
            
            queue_name = getattr(settings, "REDIS_QUEUE_NAME", "doffair:notifications")
            self._queue = Queue(queue_name, connection=self._redis_conn)
            
            logger.info(f"✅ Event publisher connected to Redis: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect Event Publisher to Redis: {str(e)}")
            raise
    
    def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: EventSource,
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
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
