"""Unit tests for Rule D: Unauthorized Access (Repeated 401/403) Detection."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.detection.detection_settings import DetectionSettings
from app.detection.rules.unauthorized_access import UnauthorizedAccessRule
from app.schemas.common import Severity, ThreatCategory
from app.schemas.detection import RequestEvent
from tests.unit.detection.conftest import FakeWindowCounter


def make_event(
    ip: str = "203.0.113.50",
    path: str = "/api/protected/resource",
    status_code: int = 403,
    user_id: Optional[int] = None,
    time_offset_sec: int = 0,
    base_time: datetime | None = None,
) -> RequestEvent:
    now = base_time or datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return RequestEvent(
        request_id=str(uuid.uuid4()),
        occurred_at=now + timedelta(seconds=time_offset_sec),
        source_ip=ip,
        path=path,
        normalized_path=path,
        method="GET",
        status_code=status_code,
        response_time_ms=25,
        user_id=user_id,
    )


def test_unauthorized_trigger_guard(fake_counter: FakeWindowCounter):
    rule = UnauthorizedAccessRule()

    # 401 on /api/auth/login MUST be ignored by Rule D (owned by Rule A)
    assert rule.evaluate(make_event(path="/api/auth/login", status_code=401), fake_counter) is None

    # 200 OK on protected resource must be ignored
    assert rule.evaluate(make_event(status_code=200), fake_counter) is None

    # 404 Not Found must be ignored
    assert rule.evaluate(make_event(status_code=404), fake_counter) is None


def test_unauthorized_threshold_boundaries(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(unauth_threshold=15, unauth_window_seconds=600)
    rule = UnauthorizedAccessRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # 15 events (combination of 401 and 403)
    for i in range(15):
        st = 401 if i % 2 == 0 else 403
        fake_counter.add_event(
            make_event(status_code=st, time_offset_sec=-100 + i, base_time=base_time)
        )

    curr_event = make_event(status_code=403, time_offset_sec=0, base_time=base_time)
    # Exactly at threshold 15 -> NO alert
    assert rule.evaluate(curr_event, fake_counter) is None

    # Add 1 more -> 16 events (threshold plus one)
    fake_counter.add_event(curr_event)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    assert result.category == ThreatCategory.UNAUTHORIZED_ACCESS
    assert result.request_count == 16
    assert result.threshold == 15
    assert result.severity == Severity.LOW
    assert result.dedup_key == "UNAUTHORIZED_ACCESS:203.0.113.50"
    assert "per_status" in result.evidence


def test_unauthorized_dedup_key_user_variant(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(unauth_threshold=10, unauth_window_seconds=600)
    rule = UnauthorizedAccessRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Events with user_id = 42
    for i in range(12):
        fake_counter.add_event(
            make_event(ip="10.0.0.1", user_id=42, time_offset_sec=-50 + i, base_time=base_time)
        )

    event_with_user = make_event(ip="10.0.0.1", user_id=42, time_offset_sec=0, base_time=base_time)
    result = rule.evaluate(event_with_user, fake_counter)
    assert result is not None
    # Must use user variant when user_id is present
    assert result.dedup_key == "UNAUTHORIZED_ACCESS:user:42"
    assert result.user_id == 42


def test_unauthorized_missing_user_id(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(unauth_threshold=5, unauth_window_seconds=600)
    rule = UnauthorizedAccessRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Events with missing user_id (None)
    for i in range(6):
        fake_counter.add_event(
            make_event(ip="10.0.0.9", user_id=None, time_offset_sec=-20 + i, base_time=base_time)
        )

    event_no_user = make_event(ip="10.0.0.9", user_id=None, time_offset_sec=0, base_time=base_time)
    result = rule.evaluate(event_no_user, fake_counter)
    assert result is not None
    # Must fall back to IP variant
    assert result.dedup_key == "UNAUTHORIZED_ACCESS:10.0.0.9"
    assert result.user_id is None
