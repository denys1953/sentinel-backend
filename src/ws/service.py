from pydantic import ValidationError
from src.conversations.schemas import MessageCreate
from src.ws.manager import WebSocketManager
from src.ws.schemas import MessageIncoming, MessageOutgoing, ErrorResponse
from src.auth.service import get_user_by_fingerprint
from src.conversations.service import handle_new_incoming_message, get_all_recipients


class ChatService:
    def __init__(self, manager: WebSocketManager, session_factory):
        self.manager = manager
        self.session_factory = session_factory

    async def process_message(self, fingerprint: str, raw_data: dict):
        async with self.session_factory() as db:
            try:
                incoming = MessageIncoming.model_validate(raw_data)
                sender = await get_user_by_fingerprint(db, fingerprint)

                if sender is None:
                    await self.manager.send_personal_message(
                        {"type": "error", "detail": "User not found"}, 
                        fingerprint
                    )
                    return

                new_message, recipients = await handle_new_incoming_message(
                    db=db,
                    sender_id=sender.id,
                    message_data=incoming
                )

                response = MessageOutgoing(
                    id=new_message.id,
                    conversation_id=new_message.conversation_id,
                    sender_fp=fingerprint,
                    content=incoming.content_encoded,
                    timestamp=new_message.created_at
                )

                payload = response.model_dump(mode="json")
                for r in recipients:
                    await self.manager.send_personal_message(payload, r.fingerprint)

            except ValidationError as e:
                error = ErrorResponse(detail=str(e))
                await self.manager.send_personal_message(
                    error.model_dump(mode="json"), 
                    fingerprint
                )