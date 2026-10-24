"""SQLAlchemy ReportArchive model (Owner: Anvi).

Follows database-contract.md:
Table: report_archives
Columns:
- id: BIGINT identity primary key
- report_type: VARCHAR(30) CHECK ('LOGS_CSV', 'ALERTS_CSV', 'SUMMARY')
- object_key: VARCHAR(512) unique
- storage_backend: VARCHAR(20) CHECK ('s3', 'local')
- content_type: VARCHAR(100)
- size_bytes: BIGINT
- sha256: CHAR(64)
- range_start, range_end: TIMESTAMPTZ
- filters: JSONB default {}
- created_by: BIGINT nullable, FK users.id ON DELETE SET NULL
- created_at: TIMESTAMPTZ index
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReportArchive(Base):
    __tablename__ = "report_archives"
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('LOGS_CSV', 'ALERTS_CSV', 'SUMMARY')",
            name="ck_report_archives_report_type",
        ),
        CheckConstraint(
            "storage_backend IN ('s3', 'local')",
            name="ck_report_archives_storage_backend",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    object_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
    )
    storage_backend: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    sha256: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
    )
    range_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    range_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    filters: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )

    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
