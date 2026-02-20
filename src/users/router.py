from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.users.schemas import UserRead

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)):
    return current_user