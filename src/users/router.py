from typing import Optional

from fastapi import APIRouter, Depends, Query, Body

from src.auth.dependencies import get_current_user
from src.users.schemas import UserPublic, UserRead
from src.core.database import get_db, AsyncSession
from src.users.service import search_users_by_username
from src.core.redis import redis_client


router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserPublic])
async def search_users(
    search: Optional[str] = Query(None, min_length=2, alias="search"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user)
):
    return await search_users_by_username(search, limit, db, current_user)

@router.post("/statuses")
async def get_user_statuses(fingerprints: list[str] = Body(...)):
    if not fingerprints:
        return {}
    
    keys = [f"online:{fp}" for fp in fingerprints]
    results = await redis_client.mget(*keys)

    return {fp: (results[i] is not None) for i, fp in enumerate(fingerprints)}
