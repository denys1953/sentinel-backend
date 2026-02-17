from datetime import UTC, datetime
from typing import TYPE_CHECKING, List

from src.core.database import Base

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # E2EE keys
    public_key: Mapped[str] = mapped_column(String, nullable=True)
    enc_private_key: Mapped[str] = mapped_column(String, nullable=True)

    # Salt for client-side password hashing
    salt: Mapped[str] = mapped_column(String, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
