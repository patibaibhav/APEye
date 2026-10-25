"""Suspicious IPs API routes (Owner: Baibhav).

Follows the API Contract and Blueprint Section 8.2:
- GET /api/suspicious-ips: List suspicious IPs with pagination and filters
- GET /api/suspicious-ips/{ip}: Get suspicious IP summary plus alerts
- PATCH /api/suspicious-ips/{ip}/investigation: Update investigation status and note
"""

import ipaddress
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.common_params import PaginationParams, TimeRangeParams
from app.api.routes.sandbox import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.repositories import ip_investigation_repository
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, ThreatCategory
from app.schemas.suspicious_ips import (
    InvestigationStatus,
    InvestigationUpdate,
    SuspiciousIpDetail,
    SuspiciousIpListItem,
)

router = APIRouter(tags=["suspicious-ips"])


def validate_ip(ip_str: str) -> str:
    """Validates that a string is a valid IPv4 or IPv6 address or raises ValidationError (422)."""
    try:
        ipaddress.ip_address(ip_str.strip())
        return ip_str.strip()
    except ValueError as exc:
        raise ValidationError(f"Invalid IP address format: {ip_str}") from exc


@router.get("", response_model=PaginatedResponse[SuspiciousIpListItem], status_code=status.HTTP_200_OK)
def list_suspicious_ips(
    status: Optional[InvestigationStatus] = Query(None, description="Filter by investigation status"),
    category: Optional[ThreatCategory] = Query(None, description="Filter by threat category"),
    source_ip: Optional[str] = Query(None, description="Filter by exact source IP"),
    time_range: TimeRangeParams = Depends(),
    pagination: PaginationParams = Depends(),
    user: Any = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> PaginatedResponse[SuspiciousIpListItem]:
    """Lists aggregated suspicious IPs derived from alerts, with pagination and filtering."""
    validated_ip = validate_ip(source_ip) if source_ip else None

    items, total = ip_investigation_repository.list_suspicious_ips(
        session=session,
        investigation_status=status,
        category=category,
        source_ip=validated_ip,
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


@router.get("/{ip}", response_model=SuspiciousIpDetail, status_code=status.HTTP_200_OK)
def get_suspicious_ip(
    ip: str,
    user: Any = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> SuspiciousIpDetail:
    """Returns suspicious IP summary plus full alert detail items."""
    validated_ip = validate_ip(ip)

    detail = ip_investigation_repository.get_suspicious_ip_detail(
        session=session,
        source_ip=validated_ip,
    )
    if detail is None:
        raise NotFoundError(f"Suspicious IP not found: {validated_ip}")

    return detail


@router.patch("/{ip}/investigation", response_model=SuspiciousIpListItem, status_code=status.HTTP_200_OK)
def update_investigation(
    ip: str,
    body: InvestigationUpdate,
    user: Any = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> SuspiciousIpListItem:
    """Updates investigation status and optional note for a suspicious IP."""
    validated_ip = validate_ip(ip)

    existing = ip_investigation_repository.get_suspicious_ip_summary(session, validated_ip)
    if existing is None:
        raise NotFoundError(f"Suspicious IP not found: {validated_ip}")

    actor_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)

    ip_investigation_repository.upsert_investigation(
        session=session,
        source_ip=validated_ip,
        status=body.status,
        note=body.note,
        updated_by=actor_id,
    )
    session.commit()

    updated = ip_investigation_repository.get_suspicious_ip_summary(session, validated_ip)
    return updated
