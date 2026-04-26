from typing import List

from src.core.database import AsyncSession, get_db
from src.conversations.schemas import MessageCreate, MessageRead, ConversationRead, MessageUpdate
from src.auth.dependencies import get_current_user
from src.conversations.service import create_message, get_messages_by_conversation, get_or_create_conversation, check_participation, get_user_conversations
from src.auth.service import get_user_by_id
from src.users.models import User

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(tags=["Conversations"])

@router.get("/", response_model=List[ConversationRead])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_user_conversations(db, current_user.id)

@router.post("/", response_model=MessageRead)
async def send_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv_id = message_data.conversation_id

    if not conv_id:
        if not message_data.recipient_id:
            raise HTTPException(status_code=400, detail="Either conversation_id or recipient_id must be provided")
    
        recipient = await get_user_by_id(db, message_data.recipient_id)
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        conversation = await get_or_create_conversation(db, message_data.recipient_id, current_user.id)
        conv_id = conversation.id
    else:
        is_participant = await check_participation(db, conv_id, current_user.id)
        if not is_participant:
            raise HTTPException(status_code=403, detail="You are not a participant of this conversation")

    return await create_message(message_data, db, conv_id, current_user.id)


@router.get("/{conversation_id}", response_model=List[MessageRead])
async def get_history(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_messages_by_conversation(db, conversation_id, limit, offset)

@router.delete("/messages/{message_id}")
async def delete_msg(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from src.conversations.service import delete_message
    from src.ws.dependencies import get_manager
    manager = get_manager()
    success = await delete_message(db, message_id, current_user.id, manager)
    if not success:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message or message not found")
    return {"status": "success"}

@router.patch("/messages/{message_id}", response_model=MessageRead)
async def update_msg(
    message_id: int,
    message_update: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from src.conversations.service import edit_message
    from src.ws.dependencies import get_manager
    manager = get_manager()
    
    updated_message = await edit_message(
        db, 
        message_id, 
        current_user.id, 
        message_update.content_encoded, 
        message_update.content_self, 
        manager
    )
    
    if not updated_message:
        raise HTTPException(status_code=403, detail="Not authorized to edit this message or message not found")
        
    return updated_message
