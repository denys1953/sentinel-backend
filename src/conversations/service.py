from src.conversations.schemas import MessageCreate
from src.core.database import AsyncSession
from src.conversations.models import ConversationType, Message, Conversation, ConversationParticipant
from src.users.models import User

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload


async def get_or_create_conversation(
    db: AsyncSession,
    recipient_id: int,
    sender_id: int
):
    query = select(Conversation).join(ConversationParticipant).options(selectinload(Conversation.participants)).where(
        ConversationParticipant.user_id.in_([sender_id, recipient_id]),
        Conversation.type == ConversationType.DIRECT
    ).group_by(Conversation.id).having(func.count(Conversation.id) == 2)

    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if conversation:
        return conversation

    new_conversation = Conversation(type=ConversationType.DIRECT)
    db.add(new_conversation)
    await db.flush()

    db.add_all([
        ConversationParticipant(conversation_id=new_conversation.id, user_id=sender_id),
        ConversationParticipant(conversation_id=new_conversation.id, user_id=recipient_id)
    ])
    
    try:
        await db.commit()
        await db.refresh(new_conversation, attribute_names=["participants", "created_at"])
        return new_conversation    
    except Exception as e:
        await db.rollback()
        raise e
    
async def handle_new_incoming_message(
    db: AsyncSession,
    sender_id: int,
    message_data: MessageCreate
):
    conv_id = message_data.conversation_id

    if conv_id is None:
        conversation = await get_or_create_conversation(db, message_data.recipient_id, sender_id)
        conv_id = conversation.id

    new_message = await create_message(
        db=db,
        conversation_id=conv_id,
        user_id=sender_id,
        message_data=message_data
    )

    recipients = await get_all_recipients(db, conv_id, sender_id)

    return new_message, recipients


async def create_message(
    message_data: MessageCreate,
    db: AsyncSession,
    conversation_id: int,
    user_id: int
):
    new_message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        content_encoded=message_data.content_encoded,
        content_self=message_data.content_self
    )

    db.add(new_message)

    update_conv_query = (
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=func.now())
    )
    await db.execute(update_conv_query)
    
    try:
        await db.commit()
        await db.refresh(new_message)
        return new_message
    except Exception as e:
        await db.rollback()
        raise e
    
async def get_messages_by_conversation(
    db: AsyncSession,
    conversation_id: int,
    limit: int,
    offset: int,
):
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    return result.scalars().all()

async def check_participation(
    db: AsyncSession,
    conversation_id: int,
    user_id: int
) -> bool:
    query = select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

async def get_all_recipients(
    db: AsyncSession,
    conversation_id: int,
    sender_id: int
):
    query = (
        select(User)
        .join(ConversationParticipant, ConversationParticipant.user_id == User.id)
        .where(
            ConversationParticipant.conversation_id == conversation_id,
            User.id != sender_id
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_conversations(
    db: AsyncSession,
    user_id: int
):
    query = (
        select(Conversation)
        .options(selectinload(Conversation.participants).selectinload(ConversationParticipant.user))
        .join(Conversation.participants)
        .where(
            ConversationParticipant.user_id == user_id,
            
        )
    )
    result = await db.execute(query)
    return result.scalars().all()