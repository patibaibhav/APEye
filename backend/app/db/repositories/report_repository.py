"""Report Archive repository implementing parameterized SQLAlchemy queries (Owner: Anvi)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.report import ReportArchive


def create_report_archive(
    session: Session,
    report_type: str,
    object_key: str,
    storage_backend: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    range_start: datetime,
    range_end: datetime,
    filters: Optional[Dict[str, Any]] = None,
    created_by: Optional[int] = None,
) -> ReportArchive:
    """Creates and persists metadata record for an uploaded report archive."""
    archive = ReportArchive(
        report_type=report_type,
        object_key=object_key,
        storage_backend=storage_backend,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        range_start=range_start,
        range_end=range_end,
        filters=filters or {},
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )
    session.add(archive)
    session.flush()
    return archive


def get_report_archive_by_id(session: Session, archive_id: int) -> Optional[ReportArchive]:
    """Retrieves a single report archive by ID."""
    stmt = select(ReportArchive).where(ReportArchive.id == archive_id)
    return session.execute(stmt).scalar_one_or_none()


def list_report_archives(
    session: Session,
    offset: int = 0,
    limit: int = 25,
) -> Tuple[List[ReportArchive], int]:
    """Lists report archives sorted by created_at DESC with pagination."""
    count_stmt = select(func.count(ReportArchive.id))
    total = session.execute(count_stmt).scalar() or 0

    stmt = (
        select(ReportArchive)
        .order_by(ReportArchive.created_at.desc(), ReportArchive.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(session.execute(stmt).scalars().all())

    return items, total
