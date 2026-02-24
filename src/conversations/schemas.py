from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from src.conversations.models import ConversationType
from src.users.schemas import UserPublic

class BaseWithID(BaseModel):
    id: int

class ParticipantBase(BaseModel):
    user_id: int
    unread_count: int = 0

class ParticipantRead(ParticipantBase):
    user: Optional[UserPublic] = None 

    model_config = ConfigDict(from_attributes=True)

class ConversationBase(BaseModel):
    type: ConversationType = ConversationType.DIRECT

class ConversationCreate(ConversationBase):
    recipient_id: int 

class ConversationRead(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    participants: List[ParticipantRead]

    model_config = ConfigDict(from_attributes=True)

class ConversationShort(BaseModel):
    id: int
    type: ConversationType
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageBase(BaseModel):
    conversation_id: Optional[int] = None
    recipient_id: Optional[int] = None
    content_encoded: str
    content_self: str

class MessageRead(BaseWithID, MessageBase):
    sender_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageCreate(MessageBase):
    pass
    