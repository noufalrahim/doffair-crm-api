import socketio
import logging
import redis.asyncio as redis
import json
import asyncio
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)

# Create a Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Wrapper for FastAPI
socket_app = socketio.ASGIApp(sio)

# Mapping of user_id to set of sid (socket IDs)
user_sessions: Dict[str, set] = {}

# Redis client for Pub/Sub
redis_client = redis.from_url(settings.REDIS_URL)

async def redis_listener():
    """
    Listens to Redis for notification messages and broadcasts them via Socket.IO
    """
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications_broadcast")
    
    logger.info("📡 Started Redis Pub/Sub listener for WebSockets")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    notification = data.get("notification")
                    
                    if user_id and notification:
                        await emit_notification(user_id, notification)
                    elif notification:
                        # Broadcast to all if no user_id
                        await broadcast_to_all('new_notification', notification)
                except Exception as e:
                    logger.error(f"❌ Error processing Redis message: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Redis listener error: {str(e)}")
    finally:
        await pubsub.unsubscribe("notifications_broadcast")

@sio.event
async def connect(sid, environ, auth):
    """
    Handle connection. 
    Expects auth token or user_id in auth or headers.
    """
    try:
        user_id = None
        
        # Check auth object
        if auth and isinstance(auth, dict) and 'user_id' in auth:
            user_id = str(auth['user_id'])
        
        # Check headers or query params
        if not user_id:
            query = environ.get('QUERY_STRING', '')
            params = dict(item.split('=') for item in query.split('&') if '=' in item)
            user_id = params.get('user_id')

        if user_id:
            if user_id not in user_sessions:
                user_sessions[user_id] = set()
            user_sessions[user_id].add(sid)
            
            await sio.enter_room(sid, f"user_{user_id}")
            logger.info(f"✅ User {user_id} connected with sid {sid}")
            
            # Send an acknowledgment or initial state if needed
            await sio.emit('connection_established', {'user_id': user_id}, room=sid)
        else:
            logger.warning(f"⚠️ Connection attempt without user_id from sid {sid}")
            
    except Exception as e:
        logger.error(f"❌ Error in connect: {str(e)}")

@sio.event
async def disconnect(sid):
    """Handle disconnection"""
    for user_id, sids in list(user_sessions.items()):
        if sid in sids:
            sids.remove(sid)
            if not sids:
                del user_sessions[user_id]
            logger.info(f"❌ User {user_id} disconnected (sid: {sid})")
            break

async def emit_notification(user_id: str, notification: Dict[str, Any]):
    """
    Broadcast notification to a specific user via WebSockets
    """
    try:
        room = f"user_{user_id}"
        await sio.emit('new_notification', notification, room=room)
        logger.info(f"📡 Broadcasted notification to user_{user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to emit notification: {str(e)}")

async def broadcast_to_all(event: str, data: Any):
    """Broadcast to all connected clients"""
    await sio.emit(event, data)
