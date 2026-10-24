"""SQLAlchemy IpInvestigation model (Owner: Anvi).

Follows database-contract.md:
Table: ip_investigations
Columns:
- source_ip: VARCHAR(45) PK
- status: VARCHAR(20) default NEW CHECK ('NEW', 'INVESTIGATING', 'RESOLVED')
- note: VARCHAR(2000) nullable
- updated_by: BIGINT nullable, FK users.id ON DELETE SET NULL
- updated_at: TIMESTAMPTZ non-null
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IpInvestigation(Base):
    __tablename__ = "ip_investigations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW', 'INVESTIGATING', 'RESOLVED')",
            name="ck_ip_investigations_status",
        ),
    )

    source_ip: Mapped[str] = mapped_column(
        String(45),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NEW",
        server_default="NEW",
    )
    note: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
