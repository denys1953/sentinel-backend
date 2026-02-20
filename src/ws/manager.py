from fastapi import WebSocket
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, fingerprint: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[fingerprint] = websocket
        logger.info(f"User {fingerprint} connected to WebSocket.")
    
    def disconnect(self, fingerprint: str):
        if fingerprint in self.active_connections:
            del self.active_connections[fingerprint]
            logger.info(f"User {fingerprint} disconnected from WebSocket.")

    async def send_personal_message(self, message: Dict[str, Any], fingerprint: str):
        websocket = self.active_connections.get(fingerprint)

        if websocket:
            await websocket.send_json(message)
            logger.info(f"Sent message to user {fingerprint}: {message}")
            return True
        return False
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)
        logger.info(f"Broadcasted message to all users: {message}")

