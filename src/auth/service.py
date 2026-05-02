import hashlib

from src.users import models
from src.users.schemas import Token, UserCreate
from ..core.security import create_access_token, hash_password, verify_password

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    query = select(models.User).where(models.User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int) -> models.User | None:
    query = select(models.User).where(models.User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_fingerprint(db: AsyncSession, fingerprint: str) -> models.User | None:
    query = select(models.User).where(models.User.fingerprint == fingerprint)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_new_user(db: AsyncSession, user_data: UserCreate) -> models.User:
    query = select(models.User).where(models.User.username == user_data.username)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )

    new_user = models.User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        public_key=user_data.public_key,
        enc_private_key=user_data.enc_private_key,
        salt=user_data.salt,
        fingerprint=hashlib.sha256(user_data.public_key.encode()).hexdigest()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Token | None:
    user = await get_user_by_username(db, username)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )

    if user.is_2fa_enabled:
        temp_token = create_access_token(data={"sub": str(user.username), "type": "2fa_temp"})
        return Token(requires_2fa=True, temp_token=temp_token)
    
    # 2FA is mandatory. If not enabled, force setup on login
    import pyotp
    import qrcode
    import io
    import base64

    # Generate a new TOTP secret if not present
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        db.add(user)
        await db.commit()

    uri = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
        name=user.username,
        issuer_name="SentinelApp"
    )
    qr = qrcode.make(uri)
    img_byte_arr = io.BytesIO()
    qr.save(img_byte_arr, format='PNG')
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()

    temp_token = create_access_token(data={"sub": str(user.username), "type": "2fa_temp"})
    return Token(
        requires_2fa=True, 
        temp_token=temp_token, 
        setup_required=True,
        qr_code=f"data:image/png;base64,{img_base64}",
        secret=user.totp_secret
    )
