"""Alert schemas for list, detail, status updates, and notes."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AlertStatus, Severity, ThreatCategory


class AlertNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    author_id: Optional[int] = None
    author_username: Optional[str] = None
    note: str
    created_at: datetime


class AlertListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: int
    category: ThreatCategory
    severity: Severity
    status: AlertStatus
    source_ip: str
    endpoints: List[str] = Field(default_factory=list)
    request_count: int
    window_seconds: int
    event_count: int
    first_detected_at: datetime
    last_detected_at: datetime


class AlertDetail(AlertListItem):
    user_id: Optional[int] = None
    threshold: int
    resolved_at: Optional[datetime] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    notes: List[AlertNoteRead] = Field(default_factory=list)
    dedup_key: Optional[str] = None


# Alias AlertRead to AlertDetail for full service output
AlertRead = AlertDetail


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


class AlertNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)
