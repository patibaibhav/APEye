"""Shared FastAPI query parameter dependencies for pagination and time-range filtering.

Follows the API Contract:
- from is inclusive, to exclusive
- both require offset or Z; naive timestamps are rejected with 422
- default: to = now(UTC), from = to - 24 hours
- maximum span: 31 days; violations return 422
- pagination: page (1-based, default 1), page_size (1-100, default 25)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Query

from app.core.errors import ValidationError


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-based page number"),
        page_size: int = Query(25, ge=1, le=100, description="Items per page (1-100)"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


def parse_iso_datetime(value: Optional[str], field_name: str) -> Optional[datetime]:
    """Parses an ISO-8601 datetime string and validates that it contains timezone offset/Z."""
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"Invalid ISO-8601 datetime format for '{field_name}': {value}") from exc

    if dt.tzinfo is None:
        raise ValidationError(f"Naive datetime without offset/Z rejected for '{field_name}': {value}")

    # Convert to UTC
    return dt.astimezone(timezone.utc)


class TimeRangeParams:
    def __init__(
        self,
        from_time: Optional[str] = Query(None, alias="from", description="ISO-8601 UTC start time (inclusive)"),
        to_time: Optional[str] = Query(None, alias="to", description="ISO-8601 UTC end time (exclusive)"),
    ) -> None:
        now = datetime.now(timezone.utc)

        parsed_to = parse_iso_datetime(to_time, "to") if to_time else now
        parsed_from = parse_iso_datetime(from_time, "from") if from_time else (parsed_to - timedelta(hours=24))

        if parsed_from >= parsed_to:
            raise ValidationError(
                f"Invalid time range: 'from' ({parsed_from.isoformat()}) must be strictly earlier than 'to' ({parsed_to.isoformat()})"
            )

        if (parsed_to - parsed_from).total_seconds() > 31 * 86400:
            raise ValidationError(
                "Time range span exceeds maximum allowable span of 31 days"
            )

        self.from_time = parsed_from
        self.to_time = parsed_to
