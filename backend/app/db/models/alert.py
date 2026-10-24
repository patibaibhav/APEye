"""SQLAlchemy Alert and AlertNote models (Owner: Anvi).

Follows database-contract.md:
Table: alerts
Columns:
- id: BIGINT identity primary key
- category, severity, status (default ACTIVE), source_ip, nullable user_id
- dedup_key VARCHAR(128), endpoints JSONB, evidence JSONB
- request_count, window_seconds, threshold, event_count (default 1)
- first_detected_at, last_detected_at, nullable resolved_at, nullable updated_by
- created_at, updated_at
Indexes:
- Partial unique dedup_key where status IN ('ACTIVE', 'INVESTIGATING')
- status, severity, category
- first_detected_at
- (source_ip, last_detected_at)

Table: alert_notes
Columns:
- id: BIGINT identity primary key
- alert_id: BIGINT FK alerts.id ON DELETE CASCADE
- author_id: BIGINT nullable (null = system), FK users.id ON DELETE SET NULL
- note: VARCHAR(2000) non-null
- created_at: TIMESTAMPTZ non-null
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            "category IN ('BRUTE_FORCE', 'EXCESSIVE_REQUESTS', 'RECONNAISSANCE', 'UNAUTHORIZED_ACCESS')",
            name="ck_alerts_category",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_alerts_severity",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INVESTIGATING', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        Index(
            "ix_alerts_dedup_active_investigating",
            "dedup_key",
            unique=True,
            postgresql_where=text("status IN ('ACTIVE', 'INVESTIGATING')"),
        ),
        Index("ix_alerts_status_severity_category", "status", "severity", "category"),
        Index("ix_alerts_first_detected_at", "first_detected_at"),
        Index("ix_alerts_source_ip_last_detected", "source_ip", "last_detected_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )
    source_ip: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    dedup_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    endpoints: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    request_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    window_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    event_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
    notes: Mapped[List["AlertNote"]] = relationship(
        "AlertNote",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="AlertNote.created_at.asc()",
    )


class AlertNote(Base):
    __tablename__ = "alert_notes"
    __table_args__ = (Index("ix_alert_notes_alert_id_created", "alert_id", "created_at"),)

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    alert_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    alert: Mapped["Alert"] = relationship("Alert", back_populates="notes")
    author: Mapped[Optional["User"]] = relationship("User", foreign_keys=[author_id])
