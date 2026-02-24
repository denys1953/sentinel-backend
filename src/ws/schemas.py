from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

from src.conversations.schemas import MessageCreate


class MessageIncoming(MessageCreate):
    pass

class MessageOutgoing(BaseModel):
    type: Literal["chat_message"] = "chat_message"
    id: int 
    sender_fp: str
    conversation_id: int
    content: str
    timestamp: datetime

class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    detail: str