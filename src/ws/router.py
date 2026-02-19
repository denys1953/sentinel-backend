from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.ws.dependencies import get_chat_service, get_manager
from src.ws.service import ChatService
from src.ws.manager import WebSocketManager

router = APIRouter(prefix="/ws", tags=["websockets"])

@router.websocket("/ws/{user_id}")
async def chat_gateway(
    websocket: WebSocket, 
    user_id: int, 
    chat_service: ChatService = Depends(get_chat_service),
    manager: WebSocketManager = Depends(get_manager)
):
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await chat_service.process_message(user_id, data)

    except WebSocketDisconnect:
        manager.disconnect(user_id)