from fastapi import WebSocket
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to WebSocket.")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket.")

    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        websocket = self.active_connections.get(user_id)

        if websocket:
            await websocket.send_json(message)
            logger.info(f"Sent message to user {user_id}: {message}")
            return True
        return False
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)
        logger.info(f"Broadcasted message to all users: {message}")

