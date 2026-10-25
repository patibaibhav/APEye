"""SQLAlchemy ApiRequestLog model (Owner: Anvi).

Follows database-contract.md:
Table: api_request_logs
Columns:
- id: BIGINT identity primary key
- request_id: VARCHAR(36) unique, non-null
- occurred_at: TIMESTAMPTZ non-null
- source_ip: VARCHAR(45) non-null
- path: VARCHAR(512) non-null
- normalized_path: VARCHAR(512) non-null
- method: VARCHAR(10) non-null
- status_code: SMALLINT non-null
- response_time_ms: INTEGER >= 0
- auth_outcome: VARCHAR(30) default NONE
- user_id: BIGINT nullable, FK users.id ON DELETE SET NULL
- created_at: TIMESTAMPTZ non-null
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"
    __table_args__ = (
        CheckConstraint(
            "response_time_ms >= 0",
            name="ck_api_request_logs_response_time_positive",
        ),
        CheckConstraint(
            "auth_outcome IN ('NONE', 'AUTHENTICATED', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'TOKEN_INVALID', 'TOKEN_EXPIRED', 'FORBIDDEN')",
            name="ck_api_request_logs_auth_outcome",
        ),
        Index("ix_api_request_logs_occurred_at", "occurred_at"),
        Index("ix_api_request_logs_source_ip_occurred", "source_ip", "occurred_at"),
        Index("ix_api_request_logs_status_occurred", "status_code", "occurred_at"),
        Index("ix_api_request_logs_norm_path_occurred", "normalized_path", "occurred_at"),
        Index(
            "ix_api_request_logs_user_occurred",
            "user_id",
            "occurred_at",
            postgresql_where=mapped_column("user_id").is_not(None),
        ),
        Index(
            "ix_api_request_logs_path_pattern",
            "path",
            postgresql_ops={"path": "varchar_pattern_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    source_ip: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )
    path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    normalized_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    status_code: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    auth_outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="NONE",
        server_default="NONE",
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
