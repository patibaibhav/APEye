"""Alert repository implementing parameterized SQLAlchemy queries (Owner: Anvi).

Fully satisfies Baibhav's alert_service and alert routes contracts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models.alert import Alert, AlertNote
from app.db.models.user import User
from app.schemas.alerts import AlertDetail, AlertListItem, AlertNoteRead
from app.schemas.common import AlertStatus, Severity, ThreatCategory
from app.schemas.detection import DetectionResult


def find_open_by_dedup_key(session: Session, dedup_key: str) -> Optional[Alert]:
    """Finds an existing open alert (status ACTIVE or INVESTIGATING) matching dedup_key."""
    stmt = select(Alert).where(
        Alert.dedup_key == dedup_key,
        Alert.status.in_(["ACTIVE", "INVESTIGATING"]),
    )
    return session.execute(stmt).scalar_one_or_none()


def touch_alert(
    session: Session,
    alert: Alert,
    last_detected_at: datetime,
    event_count: int,
    evidence: Dict[str, Any],
    request_count: int,
    endpoints: List[str],
    severity: Any,
) -> Alert:
    """Updates last activity, counts, evidence, endpoints, and severity of an open alert."""
    severity_val = severity.value if hasattr(severity, "value") else str(severity)
    alert.last_detected_at = last_detected_at
    alert.event_count = event_count
    alert.evidence = evidence
    alert.request_count = request_count
    alert.endpoints = endpoints
    alert.severity = severity_val
    alert.updated_at = datetime.now(timezone.utc)
    session.flush()
    return alert


def set_status(
    session: Session,
    alert: Alert,
    status: Any,
    actor_id: Optional[int],
    resolved_at: Optional[datetime],
) -> Alert:
    """Updates alert status, updated_by, resolved_at, and updated_at."""
    status_val = status.value if hasattr(status, "value") else str(status)
    alert.status = status_val
    alert.updated_by = actor_id
    alert.resolved_at = resolved_at
    alert.updated_at = datetime.now(timezone.utc)
    session.flush()
    return alert


def add_note(
    session: Session,
    alert_id: int,
    author_id: Optional[int],
    note: str,
    created_at: Optional[datetime] = None,
) -> AlertNoteRead:
    """Appends an analyst or system note to an alert."""
    note_entry = AlertNote(
        alert_id=alert_id,
        author_id=author_id,
        note=note,
        created_at=created_at or datetime.now(timezone.utc),
    )
    session.add(note_entry)
    session.flush()

    author_username = None
    if author_id:
        author = session.execute(
            select(User.username).where(User.id == author_id)
        ).scalar_one_or_none()
        author_username = author

    return AlertNoteRead(
        id=note_entry.id,
        alert_id=note_entry.alert_id,
        author_id=note_entry.author_id,
        author_username=author_username,
        note=note_entry.note,
        created_at=note_entry.created_at,
    )


def create_alert(session: Session, result: DetectionResult) -> Alert:
    """Creates a new ACTIVE alert from a DetectionResult."""
    cat_val = result.category.value if hasattr(result.category, "value") else str(result.category)
    sev_val = result.severity.value if hasattr(result.severity, "value") else str(result.severity)

    new_alert = Alert(
        category=cat_val,
        severity=sev_val,
        status="ACTIVE",
        source_ip=result.source_ip,
        user_id=result.user_id,
        dedup_key=result.dedup_key,
        endpoints=result.endpoints,
        evidence=result.evidence,
        request_count=result.request_count,
        window_seconds=result.window_seconds,
        threshold=result.threshold,
        event_count=1,
        first_detected_at=result.detected_at,
        last_detected_at=result.detected_at,
    )
    session.add(new_alert)
    session.flush()
    return new_alert


def get_alert_by_id(session: Session, alert_id: int) -> Optional[Alert]:
    """Retrieves an alert by ID."""
    stmt = select(Alert).where(Alert.id == alert_id)
    return session.execute(stmt).scalar_one_or_none()


def get_alert_detail(session: Session, alert_id: int) -> Optional[AlertDetail]:
    """Retrieves full alert detail including notes with author usernames."""
    stmt = (
        select(Alert)
        .options(joinedload(Alert.notes).joinedload(AlertNote.author))
        .where(Alert.id == alert_id)
    )
    alert = session.execute(stmt).unique().scalar_one_or_none()
    if alert is None:
        return None

    notes_dto = [
        AlertNoteRead(
            id=n.id,
            alert_id=n.alert_id,
            author_id=n.author_id,
            author_username=n.author.username if n.author else None,
            note=n.note,
            created_at=n.created_at,
        )
        for n in alert.notes
    ]

    return AlertDetail(
        id=alert.id,
        category=ThreatCategory(alert.category),
        severity=Severity(alert.severity),
        status=AlertStatus(alert.status),
        source_ip=alert.source_ip,
        endpoints=alert.endpoints or [],
        request_count=alert.request_count,
        window_seconds=alert.window_seconds,
        event_count=alert.event_count,
        first_detected_at=alert.first_detected_at,
        last_detected_at=alert.last_detected_at,
        user_id=alert.user_id,
        threshold=alert.threshold,
        resolved_at=alert.resolved_at,
        evidence=alert.evidence or {},
        notes=notes_dto,
        dedup_key=alert.dedup_key,
    )


def _build_alert_filters(
    severity: Optional[Any] = None,
    category: Optional[Any] = None,
    status: Optional[Any] = None,
    source_ip: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Any]:
    filters = []
    if severity:
        sev_val = severity.value if hasattr(severity, "value") else str(severity)
        filters.append(Alert.severity == sev_val)
    if category:
        cat_val = category.value if hasattr(category, "value") else str(category)
        filters.append(Alert.category == cat_val)
    if status:
        stat_val = status.value if hasattr(status, "value") else str(status)
        filters.append(Alert.status == stat_val)
    if source_ip:
        filters.append(Alert.source_ip == source_ip)
    if start:
        # Per API contract: Alert dates filter first_detected_at
        filters.append(Alert.first_detected_at >= start)
    if end:
        filters.append(Alert.first_detected_at < end)
    return filters


def list_alerts(
    session: Session,
    severity: Optional[Any] = None,
    category: Optional[Any] = None,
    status: Optional[Any] = None,
    source_ip: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 25,
) -> Tuple[List[AlertListItem], int]:
    """Lists alerts sorted by last_detected_at DESC, id DESC with pagination and filters."""
    filters = _build_alert_filters(
        severity=severity,
        category=category,
        status=status,
        source_ip=source_ip,
        start=start,
        end=end,
    )

    count_stmt = select(func.count(Alert.id))
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar() or 0

    stmt = select(Alert)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Alert.last_detected_at.desc(), Alert.id.desc()).offset(offset).limit(limit)

    rows = session.execute(stmt).scalars().all()
    items = [
        AlertListItem(
            id=a.id,
            category=ThreatCategory(a.category),
            severity=Severity(a.severity),
            status=AlertStatus(a.status),
            source_ip=a.source_ip,
            endpoints=a.endpoints or [],
            request_count=a.request_count,
            window_seconds=a.window_seconds,
            event_count=a.event_count,
            first_detected_at=a.first_detected_at,
            last_detected_at=a.last_detected_at,
        )
        for a in rows
    ]
    return items, total


def count_alerts_for_export(
    session: Session,
    severity: Optional[Any] = None,
    category: Optional[Any] = None,
    status: Optional[Any] = None,
    source_ip: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> int:
    """Returns count of matching alerts for export."""
    filters = _build_alert_filters(
        severity=severity,
        category=category,
        status=status,
        source_ip=source_ip,
        start=start,
        end=end,
    )
    stmt = select(func.count(Alert.id))
    if filters:
        stmt = stmt.where(*filters)
    return session.execute(stmt).scalar() or 0


def fetch_alerts_for_export(
    session: Session,
    severity: Optional[Any] = None,
    category: Optional[Any] = None,
    status: Optional[Any] = None,
    source_ip: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[Alert]:
    """Fetches alerts for export sorted by first_detected_at DESC, id DESC."""
    filters = _build_alert_filters(
        severity=severity,
        category=category,
        status=status,
        source_ip=source_ip,
        start=start,
        end=end,
    )
    stmt = select(Alert)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Alert.first_detected_at.desc(), Alert.id.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars().all())
