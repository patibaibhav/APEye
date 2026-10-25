"""Alerts API routes (Owner: Baibhav).

Follows the API Contract:
- GET /api/alerts: List alerts with filtering and pagination
- GET /api/alerts/{id}: Get alert detail
- PATCH /api/alerts/{id}/status: Transition alert status
- POST /api/alerts/{id}/notes: Add note to alert
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.common_params import PaginationParams, TimeRangeParams
from app.api.routes.sandbox import get_current_user
from app.core.errors import AlertNotFoundError
from app.schemas.alerts import (
    AlertDetail,
    AlertListItem,
    AlertNoteCreate,
    AlertNoteRead,
    AlertStatusUpdate,
)
from app.schemas.common import AlertStatus, PaginatedResponse, Severity, ThreatCategory
from app.services import alert_service

router = APIRouter(tags=["alerts"])


def get_db_session() -> Any:
    """Dependency yielding a database session when available."""
    try:
        from app.db.session import get_db
        yield from get_db()
    except Exception:
        yield None


def get_alert_repository() -> Any:
    """Dependency resolving alert repository functions."""
    try:
        from app.db.repositories import alert_repository
        return alert_repository
    except ImportError:
        return None


@router.get("", response_model=PaginatedResponse[AlertListItem])
def list_alerts(
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    category: Optional[ThreatCategory] = Query(None, description="Filter by category"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    source_ip: Optional[str] = Query(None, description="Exact validated source IP"),
    time_range: TimeRangeParams = Depends(),
    pagination: PaginationParams = Depends(),
    user: Any = Depends(get_current_user),
    session: Any = Depends(get_db_session),
    repo: Any = Depends(get_alert_repository),
) -> PaginatedResponse[AlertListItem]:
    """Lists alerts sorted by last_detected_at descending with optional filtering."""
    if repo and hasattr(repo, "list_alerts"):
        items, total = repo.list_alerts(
            session=session,
            severity=severity,
            category=category,
            status=status,
            source_ip=source_ip,
            start=time_range.from_time,
            end=time_range.to_time,
            offset=pagination.offset,
            limit=pagination.limit,
        )
        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
        return PaginatedResponse(
            items=items,
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        )

    # Empty response envelope when repository is not yet implemented
    return PaginatedResponse(
        items=[],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=0,
        total_pages=0,
    )


@router.get("/{id}", response_model=AlertDetail)
def get_alert(
    id: int,
    user: Any = Depends(get_current_user),
    session: Any = Depends(get_db_session),
    repo: Any = Depends(get_alert_repository),
) -> AlertDetail:
    """Returns full alert detail including evidence and notes."""
    if repo:
        if hasattr(repo, "get_alert_detail"):
            alert = repo.get_alert_detail(session, id)
        elif hasattr(repo, "get_alert_by_id"):
            alert = repo.get_alert_by_id(session, id)
        else:
            alert = None

        if alert is not None:
            return alert

    raise AlertNotFoundError(f"Alert with ID {id} not found")


@router.patch("/{id}/status", response_model=AlertDetail)
def update_alert_status(
    id: int,
    body: AlertStatusUpdate,
    user: Any = Depends(get_current_user),
    session: Any = Depends(get_db_session),
    repo: Any = Depends(get_alert_repository),
) -> AlertDetail:
    """Transitions alert status according to the frozen state machine."""
    actor_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else 1)
    updated_alert = alert_service.change_status(
        session=session,
        alert_id=id,
        new_status=body.status,
        actor_id=actor_id,
        alert_repo=repo,
    )
    return updated_alert


@router.post("/{id}/notes", response_model=AlertNoteRead, status_code=status.HTTP_201_CREATED)
def create_alert_note(
    id: int,
    body: AlertNoteCreate,
    user: Any = Depends(get_current_user),
    session: Any = Depends(get_db_session),
    repo: Any = Depends(get_alert_repository),
) -> AlertNoteRead:
    """Appends an analyst note (1 to 2000 chars) to an alert."""
    author_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    created_note = alert_service.add_note(
        session=session,
        alert_id=id,
        author_id=author_id,
        note=body.note,
        alert_repo=repo,
    )
    return created_note
