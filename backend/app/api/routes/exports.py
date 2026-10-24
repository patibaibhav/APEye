"""Exports API routes (Owner: Anvi).

Endpoints:
- GET /api/exports/logs.csv
- GET /api/exports/alerts.csv
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.common_params import TimeRangeParams
from app.api.routes.logs import validate_http_method, validate_ip_address
from app.auth.dependencies import require_user
from app.core.errors import ExportTooLargeError
from app.db.repositories import alert_repository, log_repository
from app.db.session import get_db
from app.schemas.common import AlertStatus, Severity, ThreatCategory
from app.services.export_service import generate_csv_string, get_export_max_rows

router = APIRouter(tags=["exports"])


@router.get("/logs.csv", status_code=status.HTTP_200_OK)
def export_logs_csv(
    source_ip: Optional[str] = Query(None, description="Exact validated source IP"),
    endpoint: Optional[str] = Query(None, description="Literal case-sensitive path prefix"),
    method: Optional[str] = Query(None, description="Exact uppercase HTTP method"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="Exact HTTP status code"),
    status_class: Optional[str] = Query(
        None, pattern="^(1xx|2xx|3xx|4xx|5xx)$", description="HTTP status class"
    ),
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> Response:
    """Exports filtered request logs as CSV without pagination, enforcing EXPORT_MAX_ROWS."""
    valid_ip = validate_ip_address(source_ip)
    valid_method = validate_http_method(method)

    max_rows = get_export_max_rows()
    count = log_repository.count_logs_for_export(
        session=session,
        source_ip=valid_ip,
        endpoint=endpoint,
        method=valid_method,
        status_code=status_code,
        status_class=status_class,
        start=time_range.from_time,
        end=time_range.to_time,
    )
    if count > max_rows:
        raise ExportTooLargeError(f"Export size {count} exceeds maximum allowed rows ({max_rows})")

    logs = log_repository.fetch_logs_for_export(
        session=session,
        source_ip=valid_ip,
        endpoint=endpoint,
        method=valid_method,
        status_code=status_code,
        status_class=status_class,
        start=time_range.from_time,
        end=time_range.to_time,
        limit=max_rows,
    )

    headers = [
        "id",
        "request_id",
        "occurred_at",
        "source_ip",
        "path",
        "method",
        "status_code",
        "response_time_ms",
        "auth_outcome",
        "user_id",
    ]
    rows = [
        [
            log.id,
            log.request_id,
            log.occurred_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            log.source_ip,
            log.path,
            log.method,
            log.status_code,
            log.response_time_ms,
            log.auth_outcome,
            log.user_id if log.user_id is not None else "",
        ]
        for log in logs
    ]

    csv_content = generate_csv_string(headers, rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="logs.csv"'},
    )


@router.get("/alerts.csv", status_code=status.HTTP_200_OK)
def export_alerts_csv(
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    category: Optional[ThreatCategory] = Query(None, description="Filter by category"),
    status_filter: Optional[AlertStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    source_ip: Optional[str] = Query(None, description="Exact validated source IP"),
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> Response:
    """Exports filtered alerts as CSV without pagination, enforcing EXPORT_MAX_ROWS."""
    valid_ip = validate_ip_address(source_ip)

    max_rows = get_export_max_rows()
    count = alert_repository.count_alerts_for_export(
        session=session,
        severity=severity,
        category=category,
        status=status_filter,
        source_ip=valid_ip,
        start=time_range.from_time,
        end=time_range.to_time,
    )
    if count > max_rows:
        raise ExportTooLargeError(f"Export size {count} exceeds maximum allowed rows ({max_rows})")

    alerts = alert_repository.fetch_alerts_for_export(
        session=session,
        severity=severity,
        category=category,
        status=status_filter,
        source_ip=valid_ip,
        start=time_range.from_time,
        end=time_range.to_time,
        limit=max_rows,
    )

    headers = [
        "id",
        "category",
        "severity",
        "status",
        "source_ip",
        "request_count",
        "window_seconds",
        "event_count",
        "first_detected_at",
        "last_detected_at",
    ]
    rows = [
        [
            a.id,
            a.category,
            a.severity,
            a.status,
            a.source_ip,
            a.request_count,
            a.window_seconds,
            a.event_count,
            a.first_detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            a.last_detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ]
        for a in alerts
    ]

    csv_content = generate_csv_string(headers, rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="alerts.csv"'},
    )
