"""Report and archival schemas (Owner: Anvi).

Follows Blueprint Section 4 & 5 and API Contract Section 8.2:
- GET /api/reports/summary
- POST /api/reports/archive
- GET /api/reports
- GET /api/reports/{id}/download
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    range: Dict[str, str]
    generated_at: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_alerts: int
    high_severity_alerts: int
    distinct_suspicious_ips: int
    threat_breakdown: Dict[str, int] = Field(default_factory=dict)
    top_suspicious_ips: List[Dict[str, Any]] = Field(default_factory=list)


class ReportArchiveCreate(BaseModel):
    report_type: str
    from_time: Optional[str] = Field(None, alias="from")
    to_time: Optional[str] = Field(None, alias="to")
    filters: Optional[Dict[str, Any]] = None


class ReportArchiveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    object_key: str
    storage_backend: str
    size_bytes: int
    created_at: datetime
    range: Dict[str, str] = Field(default_factory=dict)


class ReportDownloadResponse(BaseModel):
    url: str
    expires_at: str
