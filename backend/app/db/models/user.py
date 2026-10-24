"""SQLAlchemy User model (Owner: Anvi).

Follows database-contract.md:
Table: users
Columns:
- id: BIGINT identity primary key
- username: VARCHAR(50) unique, non-null
- password_hash: VARCHAR(255) non-null
- role: VARCHAR(20) non-null CHECK ('ADMIN', 'ANALYST')
- is_active: BOOLEAN default true
- created_at: TIMESTAMPTZ non-null
- last_login_at: TIMESTAMPTZ nullable
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('ADMIN', 'ANALYST')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
