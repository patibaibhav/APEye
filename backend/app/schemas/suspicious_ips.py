"""Schemas for Suspicious IP endpoints (Owner: Baibhav).

Follows the API contract:
- GET /api/suspicious-ips: Paginated list of SuspiciousIpListItem
- GET /api/suspicious-ips/{ip}: SuspiciousIpDetail with related alerts
- PATCH /api/suspicious-ips/{ip}/investigation: InvestigationUpdate -> SuspiciousIpListItem
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.alerts import AlertListItem
from app.schemas.common import ThreatCategory


class InvestigationStatus(str, Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class SuspiciousIpListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    source_ip: str
    suspicious_request_count: int
    categories: List[ThreatCategory]
    latest_activity: datetime
    alert_count: int
    open_alert_count: int
    related_alert_ids: List[int] = Field(default_factory=list)
    investigation_status: InvestigationStatus = InvestigationStatus.NEW
    investigation_note: Optional[str] = None


class SuspiciousIpDetail(SuspiciousIpListItem):
    alerts: List[AlertListItem] = Field(default_factory=list)


class InvestigationUpdate(BaseModel):
    status: InvestigationStatus
    note: Optional[str] = Field(None, max_length=2000)
