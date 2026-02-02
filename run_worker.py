"""
Worker entry point for processing notification queue
Run this to start consuming jobs from Redis queue

Usage:
    python run_worker.py

Press Ctrl+C to stop the worker
"""
import sys
from redis import Redis
from rq import Worker, Queue, Connection
from rq.timeouts import BaseDeathPenalty
from core.config import settings


# Windows-compatible death penalty class (no-op)
class WindowsDeathPenalty(BaseDeathPenalty):
    """No-op death penalty for Windows (no SIGALRM support)"""
    def setup_death_penalty(self):
        pass  # Do nothing on Windows
    
    def cancel_death_penalty(self):
        pass  # Do nothing on Windows

# Redis connection
redis_conn = Redis.from_url(settings.REDIS_URL, decode_responses=False)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Notification Worker")
    print("=" * 60)
    print(f"📡 Redis URL: {settings.REDIS_URL}")
    print(f"📋 Queue Name: {settings.REDIS_QUEUE_NAME}")
    print(f"⏰ Listening for jobs... (Press Ctrl+C to quit)")
    print("=" * 60)
    print()
    
    try:
        with Connection(redis_conn):
            # Create queue instance
            queue = Queue(settings.REDIS_QUEUE_NAME, connection=redis_conn)
            
            # Create worker - use SimpleWorker for Windows compatibility
            from rq import SimpleWorker
            
            # Disable death penalty completely for Windows (no SIGALRM support)
            worker = SimpleWorker(
                [queue], 
                connection=redis_conn,
                disable_default_exception_handler=False
            )
            worker.death_penalty_class = WindowsDeathPenalty  # Use custom no-op death penalty
            
            # Start working
            worker.work(with_scheduler=True)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⏸️  Worker stopped by user")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Worker error: {str(e)}")
        sys.exit(1)
