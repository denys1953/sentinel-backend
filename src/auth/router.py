from src.core.database import get_db
from src.users.schemas import Token, UserCreate, UserRead
from src.auth.schemas import Login2FA
from .service import authenticate_user, create_new_user

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from src.core.config import settings
from sqlalchemy.future import select
from src.users.models import User
import pyotp
from fastapi import HTTPException, status
from src.core.security import create_access_token


router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserRead)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_new_user(db, user_data)


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    auth_result = await authenticate_user(db, form_data.username, form_data.password)
    return auth_result


@router.post("/login/2fa", response_model=Token)
async def login_user_2fa(
    data: Login2FA, db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(
            data.temp_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        token_type = payload.get("type")
        if username is None or token_type != "2fa_temp":
            raise HTTPException(status_code=401, detail="Invalid temp token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid temp token")

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.totp_secret:
        raise HTTPException(status_code=401, detail="2FA not configured")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    if not user.is_2fa_enabled:
        user.is_2fa_enabled = True
        await db.commit()

    token = create_access_token(data={"sub": str(user.username)})
    return Token(access_token=token)
