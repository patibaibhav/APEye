"""Detection interfaces: WindowCounter protocol and Rule protocol.

CRITICAL: Must not import SQLAlchemy, FastAPI, or boto3.
"""

from datetime import datetime
from typing import Optional, Protocol, Sequence

from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, EndpointProfile, RequestEvent


class WindowCounter(Protocol):
    """Protocol for querying historical request event metrics over half-open time windows (start, end]."""

    def count_requests(self, *, source_ip: str, start: datetime, end: datetime) -> int:
        """Count total requests from source_ip in (start, end]."""
        ...

    def count_by_status(
        self,
        *,
        statuses: Sequence[int],
        start: datetime,
        end: datetime,
        source_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        exclude_path: Optional[str] = None,
    ) -> int:
        """Count requests matching status codes in (start, end], optionally filtered by IP or user_id."""
        ...

    def count_login_failures(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count 401 POST login failures from source_ip in (start, end]."""
        ...

    def has_login_success(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> bool:
        """Check if any successful login occurred from source_ip in (start, end]."""
        ...

    def endpoint_profile(
        self,
        *,
        source_ip: str,
        start: datetime,
        end: datetime,
    ) -> EndpointProfile:
        """Return endpoint activity summary for source_ip in (start, end]."""
        ...


class Rule(Protocol):
    """Protocol for a detection rule."""

    category: ThreatCategory

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        """Evaluate a request event against the window counter. Return DetectionResult if triggered."""
        ...
