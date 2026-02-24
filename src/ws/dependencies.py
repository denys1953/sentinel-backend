from functools import cache
from src.ws.manager import WebSocketManager
from src.ws.service import ChatService
from src.core.database import SessionLocal
from fastapi import Depends

@cache
def get_manager() -> WebSocketManager:
    return WebSocketManager()

def get_chat_service(manager: WebSocketManager = Depends(get_manager)) -> ChatService:
    return ChatService(manager, SessionLocal)