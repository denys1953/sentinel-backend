from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user
from src.users.schemas import UserPublic
from src.core.database import get_db, AsyncSession
from src.users.service import search_users_by_username

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserPublic])
async def search_users(
    search: Optional[str] = Query(None, min_length=2, alias="search"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user)
):
    return await search_users_by_username(search, limit, db, current_user)