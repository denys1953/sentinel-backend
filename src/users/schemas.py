from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    public_key: str
    enc_private_key: str 
    salt: str


class UserRead(UserBase):
    id: int
    avatar_url: Optional[str] = None
    public_key: Optional[str] = None
    enc_private_key: Optional[str] = None
    salt: Optional[str] = None
    fingerprint: Optional[str] = None
    is_active: bool
    is_2fa_enabled: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserPublic(UserBase):
    id: int
    username: str
    avatar_url: Optional[str] = None 
    public_key: Optional[str] = None
    fingerprint: Optional[str] = None
    is_2fa_enabled: bool = False

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    temp_token: Optional[str] = None
    setup_required: bool = False
    qr_code: Optional[str] = None
    secret: Optional[str] = None
