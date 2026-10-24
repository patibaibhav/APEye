"""Request Logs API routes (Owner: Anvi).

Endpoints:
- GET /api/logs (Paginated, filtered list of API request logs)
- GET /api/logs/{id} (Single request log detail)
"""

import ipaddress
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.common_params import PaginationParams, TimeRangeParams
from app.auth.dependencies import require_user
from app.core.errors import NotFoundError, ValidationError
from app.db.repositories import log_repository
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.logs import ApiRequestLogRead

router = APIRouter(tags=["logs"])

VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def validate_ip_address(ip_str: Optional[str]) -> Optional[str]:
    """Validates exact IP address format (IPv4 or IPv6) or raises ValidationError."""
    if not ip_str:
        return None
    try:
        ipaddress.ip_address(ip_str)
        return ip_str
    except ValueError as exc:
        raise ValidationError(f"Invalid IP address format: {ip_str}") from exc


def validate_http_method(method_str: Optional[str]) -> Optional[str]:
    """Validates uppercase HTTP method or raises ValidationError."""
    if not method_str:
        return None
    if method_str != method_str.upper() or method_str not in VALID_HTTP_METHODS:
        raise ValidationError(f"Method must be a valid uppercase HTTP verb: {method_str}")
    return method_str


@router.get("", response_model=PaginatedResponse[ApiRequestLogRead], status_code=status.HTTP_200_OK)
def list_logs(
    source_ip: Optional[str] = Query(None, description="Exact validated source IP"),
    endpoint: Optional[str] = Query(None, description="Literal case-sensitive path prefix"),
    method: Optional[str] = Query(None, description="Exact uppercase HTTP method"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="Exact HTTP status code"),
    status_class: Optional[str] = Query(
        None, pattern="^(1xx|2xx|3xx|4xx|5xx)$", description="HTTP status class"
    ),
    time_range: TimeRangeParams = Depends(),
    pagination: PaginationParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> PaginatedResponse[ApiRequestLogRead]:
    """Lists request logs sorted by occurred_at DESC, id DESC with pagination and combined filters."""
    valid_ip = validate_ip_address(source_ip)
    valid_method = validate_http_method(method)

    items, total = log_repository.list_logs(
        session=session,
        source_ip=valid_ip,
        endpoint=endpoint,
        method=valid_method,
        status_code=status_code,
        status_class=status_class,
        start=time_range.from_time,
        end=time_range.to_time,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return PaginatedResponse(
        items=[ApiRequestLogRead.model_validate(log) for log in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
        total_pages=total_pages,
    )


@router.get("/{id}", response_model=ApiRequestLogRead, status_code=status.HTTP_200_OK)
def get_log(
    id: int,
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> ApiRequestLogRead:
    """Retrieves full details for a single request log by ID."""
    log = log_repository.get_log_by_id(session, id)
    if log is None:
        raise NotFoundError(f"Log with ID {id} not found")
    return ApiRequestLogRead.model_validate(log)
