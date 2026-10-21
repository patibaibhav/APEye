"""Unit tests for common query parameters (time-range validation and pagination)."""

import pytest

from app.api.common_params import PaginationParams, TimeRangeParams, parse_iso_datetime
from app.core.errors import ValidationError


def test_parse_iso_datetime_valid():
    dt = parse_iso_datetime("2026-01-15T10:30:00Z", "from")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.hour == 10
    assert dt.tzinfo is not None


def test_parse_iso_datetime_with_offset():
    dt = parse_iso_datetime("2026-01-15T15:30:00+05:00", "from")
    assert dt is not None
    # Converted to UTC -> 10:30 UTC
    assert dt.hour == 10


def test_parse_iso_datetime_invalid_string():
    with pytest.raises(ValidationError):
        parse_iso_datetime("not-a-date", "from")


def test_time_range_params_defaults():
    params = TimeRangeParams(from_time=None, to_time=None)
    assert params.from_time < params.to_time
    diff = params.to_time - params.from_time
    # Default is 24 hours
    assert abs(diff.total_seconds() - 86400) < 5


def test_time_range_params_invalid_ordering():
    # from >= to must raise ValidationError (422)
    with pytest.raises(ValidationError, match="must be strictly earlier"):
        TimeRangeParams(
            from_time="2026-01-15T12:00:00Z",
            to_time="2026-01-15T10:00:00Z",
        )


def test_time_range_params_exceeding_31_days():
    # Span > 31 days must raise ValidationError (422)
    with pytest.raises(ValidationError, match="maximum allowable span of 31 days"):
        TimeRangeParams(
            from_time="2026-01-01T00:00:00Z",
            to_time="2026-02-15T00:00:00Z",
        )


def test_pagination_params():
    p1 = PaginationParams(page=1, page_size=25)
    assert p1.offset == 0
    assert p1.limit == 25

    p2 = PaginationParams(page=3, page_size=10)
    assert p2.offset == 20
    assert p2.limit == 10
