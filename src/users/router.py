from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, Body, UploadFile, File, HTTPException
from pydantic import BaseModel
from src.auth.dependencies import get_current_user
from src.users.schemas import UserPublic, UserRead
from src.auth.schemas import Verify2FA
from src.core.database import get_db, AsyncSession
from src.users.service import search_users_by_username
from src.core.redis import redis_client
from src.core.config import settings
from src.core.s3 import s3_client

import pyotp
import qrcode
import io
import base64

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

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Unable to get file name")
    
    file_ext = file.filename.split('.')[-1]
    file_key = f"avatars/{uuid.uuid4()}.{file_ext}"

    s3_client.upload_fileobj(
        file.file,
        settings.AWS_S3_BUCKET_NAME,
        file_key,
        ExtraArgs={"ContentType": file.content_type}
    )

    avatar_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
    current_user.avatar_url = avatar_url
    return {"avatar_url": avatar_url}


@router.post("/me/2fa/setup")
async def setup_2fa(
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):  
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    totp_secret = pyotp.random_base32()
    
    current_user.totp_secret = totp_secret
    await db.commit()
    
    uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=current_user.username,
        issuer_name="SentinelApp"
    )
    
    qr = qrcode.make(uri)
    img_byte_arr = io.BytesIO()
    qr.save(img_byte_arr, format='PNG')
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    return {
        "secret": totp_secret,
        "qr_code": f"data:image/png;base64,{img_base64}"
    }


@router.post("/me/2fa/verify")
async def verify_2fa(
    data: Verify2FA,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
        
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA setup not initiated")
        
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
    current_user.is_2fa_enabled = True
    await db.commit()
    
    return {"message": "2FA enabled successfully"}

@router.post("/me/2fa/disable")
async def disable_2fa(
    data: Verify2FA,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
        
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    await db.commit()
    
    return {"message": "2FA disabled successfully"}