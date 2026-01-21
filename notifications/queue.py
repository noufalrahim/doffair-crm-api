"""
Queue utilities for managing notification jobs
Uses Redis Queue (RQ) for asynchronous task processing
"""
from redis import Redis
from rq import Queue, Retry
from core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NotificationQueue:
    """
    Singleton queue manager for notification jobs
    Handles connection to Redis and job enqueueing
    """
    
    _instance = None
    _redis_conn: Optional[Redis] = None
    _queue: Optional[Queue] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationQueue, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_conn is None:
            self._connect()
    
    def _connect(self):
        """Initialize Redis connection and queue"""
        try:
            self._redis_conn = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self._redis_conn.ping()
            
            # Initialize queue
            self._queue = Queue(
                name=settings.REDIS_QUEUE_NAME,
                connection=self._redis_conn,
                default_timeout='10m'  # 10 minutes timeout for each job
            )
            
            logger.info(f"✅ Connected to Redis at {settings.REDIS_URL}")
            logger.info(f"✅ Queue initialized: {settings.REDIS_QUEUE_NAME}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {str(e)}")
            raise
    
    def enqueue_notification(
        self,
        notification_id: str,
        job_timeout: str = '5m',
        retry_max: Optional[int] = None
    ) -> str:
        """
        Enqueue a notification job for background processing
        
        Args:
            notification_id: ID of the notification to process
            job_timeout: Maximum time for job execution (default: 5 minutes)
            retry_max: Maximum retry attempts (default: from config)
        
        Returns:
            Job ID from RQ
        """
        if retry_max is None:
            retry_max = settings.NOTIFICATION_RETRY_MAX
        
        try:
            # Enqueue job with retry strategy
            # Note: job_timeout=None disables timeout completely for Windows compatibility
            job = self._queue.enqueue(
                'notifications.worker.process_notification_sync',  # Function to call
                notification_id,  # Argument
                job_timeout=None,  # None = no timeout (Windows compatible)
                retry=Retry(
                    max=retry_max,
                    interval=[30, 60, 120]  # Retry after 30s, 60s, 120s
                ),
                job_id=f"notification:{notification_id}",  # Unique job ID
                description=f"Process notification {notification_id}"
            )
            
            logger.info(f"✅ Notification {notification_id} enqueued. Job ID: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"❌ Failed to enqueue notification {notification_id}: {str(e)}")
            raise
    
    def get_queue_info(self) -> dict:
        """Get current queue statistics"""
        if self._queue is None:
            return {"error": "Queue not initialized"}
        
        try:
            return {
                "name": self._queue.name,
                "count": len(self._queue),
                "started_jobs": self._queue.started_job_registry.count,
                "finished_jobs": self._queue.finished_job_registry.count,
                "failed_jobs": self._queue.failed_job_registry.count,
                "scheduled_jobs": self._queue.scheduled_job_registry.count,
            }
        except Exception as e:
            logger.error(f"Error getting queue info: {str(e)}")
            return {"error": str(e)}
    
    def clear_failed_jobs(self) -> int:
        """Clear all failed jobs from the queue"""
        if self._queue is None:
            return 0
        
        try:
            failed_registry = self._queue.failed_job_registry
            count = failed_registry.count
            failed_registry.empty()
            logger.info(f"Cleared {count} failed jobs")
            return count
        except Exception as e:
            logger.error(f"Error clearing failed jobs: {str(e)}")
            return 0
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            if self._redis_conn:
                self._redis_conn.ping()
                return True
            return False
        except Exception:
            return False


# Singleton instance
notification_queue = NotificationQueue()
