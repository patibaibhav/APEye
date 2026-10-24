"""Dashboard API routes (Owner: Anvi).

Endpoints:
- GET /api/dashboard/summary
- GET /api/dashboard/traffic
- GET /api/dashboard/status-distribution
- GET /api/dashboard/top-endpoints
- GET /api/dashboard/response-times
- GET /api/dashboard/alert-severity
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.common_params import TimeRangeParams
from app.auth.dependencies import require_user
from app.db.repositories import dashboard_repository
from app.db.session import get_db
from app.schemas.dashboard import (
    AlertSeverityResponse,
    DashboardSummary,
    ResponseTimesResponse,
    StatusDistributionResponse,
    TopEndpointsResponse,
    TrafficResponse,
)

router = APIRouter(tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, status_code=status.HTTP_200_OK)
def get_summary(
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> DashboardSummary:
    """Returns overview metrics: total requests, successes, failures, alerts, and distinct suspicious IPs."""
    data = dashboard_repository.get_dashboard_summary(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
    )
    return DashboardSummary(**data)


@router.get("/traffic", response_model=TrafficResponse, status_code=status.HTTP_200_OK)
def get_traffic(
    interval: str = Query("1h", description="Bucket interval (e.g. 1m, 5m, 1h, 1d)"),
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> TrafficResponse:
    """Returns zero-filled time series of total, successful, and failed request counts."""
    data = dashboard_repository.get_dashboard_traffic(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
        interval_str=interval,
    )
    return TrafficResponse(**data)


@router.get(
    "/status-distribution",
    response_model=StatusDistributionResponse,
    status_code=status.HTTP_200_OK,
)
def get_status_distribution(
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> StatusDistributionResponse:
    """Returns distribution breakdown of HTTP status classes and individual status codes."""
    data = dashboard_repository.get_dashboard_status_distribution(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
    )
    return StatusDistributionResponse(**data)


@router.get("/top-endpoints", response_model=TopEndpointsResponse, status_code=status.HTTP_200_OK)
def get_top_endpoints(
    limit: int = Query(10, ge=1, le=20, description="Maximum endpoints to return (1-20)"),
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> TopEndpointsResponse:
    """Returns highest traffic normalized endpoints with corresponding error volumes."""
    items = dashboard_repository.get_dashboard_top_endpoints(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
        limit=limit,
    )
    return TopEndpointsResponse(items=items)


@router.get("/response-times", response_model=ResponseTimesResponse, status_code=status.HTTP_200_OK)
def get_response_times(
    interval: str = Query("1h", description="Bucket interval (e.g. 1m, 5m, 1h, 1d)"),
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> ResponseTimesResponse:
    """Returns avg, p95, and max response times per time bucket, zero-filled."""
    data = dashboard_repository.get_dashboard_response_times(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
        interval_str=interval,
    )
    return ResponseTimesResponse(**data)


@router.get("/alert-severity", response_model=AlertSeverityResponse, status_code=status.HTTP_200_OK)
def get_alert_severity(
    time_range: TimeRangeParams = Depends(),
    user: Any = Depends(require_user),
    session: Session = Depends(get_db),
) -> AlertSeverityResponse:
    """Returns alert counts grouped by severity, guaranteed to always include LOW, MEDIUM, and HIGH."""
    items = dashboard_repository.get_dashboard_alert_severity(
        session=session,
        start=time_range.from_time,
        end=time_range.to_time,
    )
    return AlertSeverityResponse(items=items)
