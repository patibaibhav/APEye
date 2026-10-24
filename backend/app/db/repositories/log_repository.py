"""API Request Log repository implementing parameterized SQLAlchemy queries (Owner: Anvi)."""

from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.log import ApiRequestLog
from app.schemas.detection import RequestEvent


def escape_like_prefix(pattern: str) -> str:
    """Escapes SQL LIKE wildcards ('%', '_', '\') so the pattern behaves as a literal prefix."""
    escaped = pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "%"


def _build_log_filters(
    source_ip: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    status_class: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Any]:
    """Builds parameterized filter criteria combined with AND."""
    filters = []

    if source_ip:
        filters.append(ApiRequestLog.source_ip == source_ip)

    if endpoint:
        like_pattern = escape_like_prefix(endpoint)
        filters.append(ApiRequestLog.path.like(like_pattern, escape="\\"))

    if method:
        filters.append(ApiRequestLog.method == method.upper())

    if status_code is not None:
        filters.append(ApiRequestLog.status_code == status_code)
    elif status_class:
        # e.g. "2xx" -> 200 to 299
        class_digit = status_class[0]
        if class_digit in ("1", "2", "3", "4", "5"):
            min_code = int(class_digit) * 100
            max_code = min_code + 99
            filters.append(ApiRequestLog.status_code.between(min_code, max_code))

    if start:
        # from is inclusive
        filters.append(ApiRequestLog.occurred_at >= start)
    if end:
        # to is exclusive
        filters.append(ApiRequestLog.occurred_at < end)

    return filters


def create_request_log(session: Session, event: RequestEvent) -> ApiRequestLog:
    """Persists a normalized RequestEvent into api_request_logs."""
    outcome_str = (
        event.auth_outcome.value
        if hasattr(event.auth_outcome, "value")
        else str(event.auth_outcome)
    )
    log_entry = ApiRequestLog(
        request_id=event.request_id,
        occurred_at=event.occurred_at,
        source_ip=event.source_ip,
        path=event.path,
        normalized_path=event.normalized_path,
        method=event.method.upper(),
        status_code=event.status_code,
        response_time_ms=event.response_time_ms,
        auth_outcome=outcome_str,
        user_id=event.user_id,
    )
    session.add(log_entry)
    session.flush()
    return log_entry


def get_log_by_id(session: Session, log_id: int) -> Optional[ApiRequestLog]:
    """Retrieves a single request log by ID."""
    stmt = select(ApiRequestLog).where(ApiRequestLog.id == log_id)
    return session.execute(stmt).scalar_one_or_none()


def list_logs(
    session: Session,
    source_ip: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    status_class: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 25,
) -> Tuple[List[ApiRequestLog], int]:
    """Lists request logs sorted by occurred_at DESC, id DESC with pagination and filters."""
    filters = _build_log_filters(
        source_ip=source_ip,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        status_class=status_class,
        start=start,
        end=end,
    )

    count_stmt = select(func.count(ApiRequestLog.id))
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar() or 0

    stmt = select(ApiRequestLog)
    if filters:
        stmt = stmt.where(*filters)

    # Sort occurred_at DESC, id DESC per API contract
    stmt = (
        stmt.order_by(ApiRequestLog.occurred_at.desc(), ApiRequestLog.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(session.execute(stmt).scalars().all())

    return items, total


def count_logs_for_export(
    session: Session,
    source_ip: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    status_class: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> int:
    """Returns total count of matching logs for export cap check."""
    filters = _build_log_filters(
        source_ip=source_ip,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        status_class=status_class,
        start=start,
        end=end,
    )
    stmt = select(func.count(ApiRequestLog.id))
    if filters:
        stmt = stmt.where(*filters)
    return session.execute(stmt).scalar() or 0


def fetch_logs_for_export(
    session: Session,
    source_ip: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    status_class: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[ApiRequestLog]:
    """Fetches logs for export sorted by occurred_at DESC, id DESC without offset."""
    filters = _build_log_filters(
        source_ip=source_ip,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        status_class=status_class,
        start=start,
        end=end,
    )
    stmt = select(ApiRequestLog)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(ApiRequestLog.occurred_at.desc(), ApiRequestLog.id.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars().all())
