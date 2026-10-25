"""Detection schemas: RequestEvent, DetectionResult, AlertOutcome, EndpointProfile."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuthOutcome, Severity, ThreatCategory


class RequestEvent(BaseModel):
    """Normalized request event constructed after HTTP response completes."""
    model_config = ConfigDict(frozen=True)

    request_id: str
    occurred_at: datetime
    source_ip: str
    path: str
    normalized_path: str
    method: str
    status_code: int
    response_time_ms: int = Field(..., ge=0)
    auth_outcome: AuthOutcome = AuthOutcome.NONE
    user_id: Optional[int] = None


class DetectionResult(BaseModel):
    """Result emitted by a detection rule evaluation."""
    model_config = ConfigDict(extra="forbid")

    category: ThreatCategory
    severity: Severity
    source_ip: str
    user_id: Optional[int] = None
    endpoints: List[str] = Field(default_factory=list)
    request_count: int
    window_seconds: int
    threshold: int
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dedup_key: str
    detected_at: datetime


class AlertOutcome(BaseModel):
    """Result of processing a DetectionResult against alert storage."""
    model_config = ConfigDict(extra="forbid")

    action: Literal["created", "updated", "auto_closed_and_created", "suppressed"]
    alert_id: Optional[int] = None


class EndpointProfile(BaseModel):
    """Aggregate request profiling used by reconnaissance detection."""
    model_config = ConfigDict(extra="forbid")

    total_requests: int
    distinct_paths: int
    error_count: int  # HTTP 400-499 errors
    top_paths: List[Tuple[str, int]] = Field(default_factory=list)
