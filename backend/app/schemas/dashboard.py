"""Dashboard analytics schemas (Owner: Anvi).

Follows Blueprint Section 4 & 5 and API Contract Section 8.2:
- GET /api/dashboard/summary
- GET /api/dashboard/traffic
- GET /api/dashboard/status-distribution
- GET /api/dashboard/top-endpoints
- GET /api/dashboard/response-times
- GET /api/dashboard/alert-severity
"""

from typing import Dict, List

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Severity


class DashboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    window: Dict[str, str]
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_alerts: int
    high_severity_alerts: int
    distinct_suspicious_ips: int


class TrafficPoint(BaseModel):
    bucket_start: str
    total: int
    successful: int
    failed: int


class TrafficResponse(BaseModel):
    interval: str
    points: List[TrafficPoint]


class StatusClassItem(BaseModel):
    status_class: str
    count: int


class StatusCodeItem(BaseModel):
    status_code: int
    count: int


class StatusDistributionResponse(BaseModel):
    classes: List[StatusClassItem]
    codes: List[StatusCodeItem]


class TopEndpointItem(BaseModel):
    endpoint: str
    request_count: int
    error_count: int


class TopEndpointsResponse(BaseModel):
    items: List[TopEndpointItem]


class ResponseTimePoint(BaseModel):
    bucket_start: str
    avg_ms: float
    p95_ms: float
    max_ms: int


class ResponseTimesResponse(BaseModel):
    interval: str
    points: List[ResponseTimePoint]


class AlertSeverityItem(BaseModel):
    severity: Severity
    count: int


class AlertSeverityResponse(BaseModel):
    items: List[AlertSeverityItem]
