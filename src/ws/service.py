from pydantic import ValidationError
from src.ws.manager import WebSocketManager
from src.ws.schemas import MessageIncoming, MessageOutgoing, ErrorResponse


class ChatService:
    def __init__(self, manager: WebSocketManager):
        self.manager = manager

    async def process_message(self, fingerprint: str, raw_data: dict):
        try:
            incoming = MessageIncoming.model_validate(raw_data)

            response = MessageOutgoing(
                sender_fp=fingerprint,
                content=incoming.content
            )

            success = await self.manager.send_personal_message(
                response.model_dump(mode="json"), 
                incoming.receiver_fp
            )

            if not success:
                pass

        except ValidationError as e:
            error = ErrorResponse(detail=str(e))
            await self.manager.send_personal_message(
                error.model_dump(mode="json"), 
                fingerprint
            )