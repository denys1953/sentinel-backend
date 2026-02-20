from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.ws.dependencies import get_chat_service, get_manager
from src.ws.service import ChatService
from src.ws.manager import WebSocketManager

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/{fingerprint}")
async def chat_gateway(
    websocket: WebSocket, 
    fingerprint: str, 
    chat_service: ChatService = Depends(get_chat_service),
    manager: WebSocketManager = Depends(get_manager)
):
    await manager.connect(fingerprint, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await chat_service.process_message(fingerprint, data)

    except WebSocketDisconnect:
        manager.disconnect(fingerprint)