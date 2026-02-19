from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class MessageIncoming(BaseModel):
    receiver_id: int
    content: str

class MessageOutgoing(BaseModel):
    type: Literal["chat_message"] = "chat_message"
    sender_id: int
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    detail: str