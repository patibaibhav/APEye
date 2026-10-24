"""Reports API routes (Owner: Anvi).

Endpoints:
- GET /api/reports/summary
- POST /api/reports/archive (ADMIN only)
- GET /api/reports
- GET /api/reports/{id}/download
- GET /api/reports/file (Local storage streaming download)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common_params import PaginationParams, TimeRangeParams, parse_iso_datetime
from app.auth.dependencies import require_role, require_user
from app.core.errors import NotFoundError, ValidationError
from app.db.models.alert import Alert
from app.db.models.report import ReportArchive
from app.db.repositories import dashboard_repository, ip_investigation_repository, report_repository
from app.db.session import get_db
from app.integrations.storage import get_storage
from app.schemas.common import PaginatedResponse
from app.schemas.reports import (
    ReportArchiveCreate,
    ReportArchiveRead,
    ReportDownloadResponse,
    ReportSummaryResponse,
)
from app.services import report_service

router = APIRouter(tags=["reports"])


def _format_archive_read(a: ReportArchive) -> ReportArchiveRead:
    return ReportArchiveRead(
        id=a.id,
        report_type=a.report_type,
        object_key=a.object_key,
        storage_backend=a.storage_backend,
        size_bytes=a.size_bytes,
        created_at=a.created_at,
        range={
            "from": a.range_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": a.range_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )


@router.get("/summary", response_model=ReportSummaryResponse, status_code=status.HTTP_200_OK)
def get_report_summary(
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> ReportSummaryResponse:
    """Returns security audit summary with request counts, alert metrics, threat breakdown, and top suspicious IPs."""
    dash = dashboard_repository.get_dashboard_summary(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
    )

    # Threat category breakdown
    cat_stmt = (
        select(Alert.category, func.count(Alert.id).label("cnt"))
        .where(
            Alert.first_detected_at >= time_range.from_time,
            Alert.first_detected_at < time_range.to_time,
        )
        .group_by(Alert.category)
    )
    cat_rows = session.execute(cat_stmt).all()
    threat_map: Dict[str, int] = {r[0]: r[1] for r in cat_rows}

    # Top suspicious IPs in window
    suspicious_ips, _ = ip_investigation_repository.list_suspicious_ips(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
        offset=0,
        limit=5,
    )
    top_ips = [
        {
            "source_ip": s.source_ip,
            "alert_count": s.alert_count,
            "suspicious_request_count": s.suspicious_request_count,
            "investigation_status": s.investigation_status.value,
        }
        for s in suspicious_ips
    ]

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return ReportSummaryResponse(
        range=dash["window"],
        generated_at=now_str,
        total_requests=dash["total_requests"],
        successful_requests=dash["successful_requests"],
        failed_requests=dash["failed_requests"],
        total_alerts=dash["total_alerts"],
        high_severity_alerts=dash["high_severity_alerts"],
        distinct_suspicious_ips=dash["distinct_suspicious_ips"],
        threat_breakdown=threat_map,
        top_suspicious_ips=top_ips,
    )


@router.post("/archive", response_model=ReportArchiveRead, status_code=status.HTTP_201_CREATED)
def create_report_archive(
    body: ReportArchiveCreate,
    admin_user: Any = Depends(require_role("ADMIN")),
    session: Session = Depends(get_db),
) -> ReportArchiveRead:
    """Generates an encrypted report archive in object storage (ADMIN only)."""
    parsed_from = parse_iso_datetime(body.from_time, "from")
    parsed_to = parse_iso_datetime(body.to_time, "to")

    if not parsed_from or not parsed_to:
        raise ValidationError("Both 'from' and 'to' datetime boundaries must be provided")

    if parsed_from >= parsed_to:
        raise ValidationError("Invalid time range: 'from' must be strictly earlier than 'to'")

    if (parsed_to - parsed_from).total_seconds() > 31 * 86400:
        raise ValidationError("Time range span exceeds maximum allowable span of 31 days")

    creator_id = getattr(admin_user, "id", None) or (
        admin_user.get("id") if isinstance(admin_user, dict) else None
    )

    archive = report_service.create_archive_artifact(
        session=session,
        report_type=body.report_type,
        start=parsed_from,
        end=parsed_to,
        filters=body.filters,
        created_by=creator_id,
    )

    return _format_archive_read(archive)


@router.get("", response_model=PaginatedResponse[ReportArchiveRead], status_code=status.HTTP_200_OK)
def list_report_archives(
    pagination: PaginationParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> PaginatedResponse[ReportArchiveRead]:
    """Lists persisted report archive artifacts with pagination."""
    items, total = report_repository.list_report_archives(
        session=session,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return PaginatedResponse(
        items=[_format_archive_read(a) for a in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
        total_pages=total_pages,
    )


@router.get("/{id}/download", response_model=ReportDownloadResponse, status_code=status.HTTP_200_OK)
def get_download_url(
    id: int,
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> ReportDownloadResponse:
    """Returns an authorized presigned URL (with expiration) to download the archived report."""
    archive = report_repository.get_report_archive_by_id(session, id)
    if archive is None:
        raise NotFoundError(f"Report archive with ID {id} not found")

    ttl = int(os.getenv("PRESIGNED_URL_TTL_SECONDS", "300"))
    storage = get_storage(archive.storage_backend)
    download_url = storage.presign_download(archive.object_key, ttl_seconds=ttl)

    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return ReportDownloadResponse(
        url=download_url,
        expires_at=expires_at,
    )


@router.get("/file", status_code=status.HTTP_200_OK)
def download_local_file(
    key: str = Query(..., description="Storage object key"),
    user: Any = Depends(require_user),
) -> Response:
    """Streams file data for local storage backend downloads (never exposes server file paths)."""
    storage = get_storage("local")
    data = storage.get_bytes(key)

    filename = os.path.basename(key)
    # Determine appropriate content type based on extension
    content_type = "application/octet-stream"
    if key.endswith(".csv.gz"):
        content_type = "application/gzip"
    elif key.endswith(".csv"):
        content_type = "text/csv"
    elif key.endswith(".md"):
        content_type = "text/markdown"

    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
