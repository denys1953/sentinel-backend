import asyncio
from fastapi import WebSocket
from typing import Any, Dict
import json
from src.core.redis import redis_client
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_tasks: Dict[str, asyncio.Task] = {}
        self.user_current_chat: Dict[str, int] = {}
    
    async def connect(self, fingerprint: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[fingerprint] = websocket
        task = asyncio.create_task(self._redis_listener(fingerprint))
        self.redis_tasks[fingerprint] = task
        logger.info(f"User {fingerprint} connected to WebSocket.")
    
    def disconnect(self, fingerprint: str):
        if fingerprint in self.active_connections:
            self.active_connections.pop(fingerprint, None)
            self.user_current_chat.pop(fingerprint, None)

            task = self.redis_tasks.pop(fingerprint, None)
            if task:
                task.cancel()
            logger.info(f"User {fingerprint} disconnected from WebSocket.")

    async def _redis_listener(self, fingerprint: str):
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"user_{fingerprint}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    ws = self.active_connections.get(fingerprint)
                    if ws:
                        await ws.send_json(data)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(f"user_{fingerprint}") 


    async def send_personal_message(self, message: Dict[str, Any], fingerprint: str):
        await redis_client.publish(f"user_{fingerprint}", json.dumps(message))

    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)
        logger.info(f"Broadcasted message to all users: {message}")

    async def set_current_chat(self, fingerprint: str, conv_id: int | None):
        if conv_id:
            self.user_current_chat[fingerprint] = conv_id
        else:
            self.user_current_chat.pop(fingerprint, None)
