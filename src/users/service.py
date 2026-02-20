from typing import Optional    

from sqlalchemy import select

from src.users.models import User
from src.core.database import AsyncSession
from src.users.schemas import UserPublic


async def search_users_by_username(
    q: Optional[str],
    limit: int,
    db: AsyncSession,
    current_user: UserPublic
):
    query = select(User).where(User.id != current_user.id)

    if q:
        query = query.where(User.username.ilike(f"%{q}%"))
    else:
        return []
    
    result = await db.execute(query.limit(limit))
    return result.scalars().all()