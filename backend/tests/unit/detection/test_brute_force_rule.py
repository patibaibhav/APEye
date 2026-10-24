"""Unit tests for Rule A: Brute Force Detection."""

import uuid
from datetime import datetime, timedelta, timezone

from app.detection.detection_settings import DetectionSettings
from app.detection.rules.brute_force import BruteForceRule
from app.schemas.common import Severity, ThreatCategory
from app.schemas.detection import RequestEvent
from tests.unit.detection.conftest import FakeWindowCounter


def make_event(
    ip: str = "203.0.113.10",
    path: str = "/api/auth/login",
    method: str = "POST",
    status_code: int = 401,
    time_offset_sec: int = 0,
    base_time: datetime | None = None,
) -> RequestEvent:
    now = base_time or datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    occurred_at = now + timedelta(seconds=time_offset_sec)
    return RequestEvent(
        request_id=str(uuid.uuid4()),
        occurred_at=occurred_at,
        source_ip=ip,
        path=path,
        normalized_path=path,
        method=method,
        status_code=status_code,
        response_time_ms=50,
    )


def test_brute_force_trigger_guard(fake_counter: FakeWindowCounter):
    rule = BruteForceRule()

    # GET to login path
    assert rule.evaluate(make_event(method="GET", status_code=401), fake_counter) is None

    # POST to non-login path
    assert rule.evaluate(make_event(path="/api/logs", status_code=401), fake_counter) is None

    # POST to login path with 200 OK
    assert rule.evaluate(make_event(status_code=200), fake_counter) is None


def test_brute_force_threshold_boundaries(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(brute_force_threshold=10, brute_force_window_seconds=300)
    rule = BruteForceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Seed exactly 10 failures in history
    for i in range(10):
        fake_counter.add_event(make_event(time_offset_sec=-(10 - i) * 10, base_time=base_time))

    # Current event is the 10th failure total (if counter only has 10)
    curr_event = make_event(time_offset_sec=0, base_time=base_time)
    # Exactly at threshold (10) -> NO alert
    assert rule.evaluate(curr_event, fake_counter) is None

    # Now add 1 more to reach 11 (threshold plus one)
    fake_counter.add_event(curr_event)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    assert result.category == ThreatCategory.BRUTE_FORCE
    assert result.request_count == 11
    assert result.threshold == 10
    assert result.severity == Severity.LOW
    assert result.dedup_key == "BRUTE_FORCE:203.0.113.10"
    assert result.evidence["login_success_after_failures"] is False


def test_brute_force_events_outside_window(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(brute_force_threshold=10, brute_force_window_seconds=300)
    rule = BruteForceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Add 10 events that happened 400 seconds ago (outside 300s window)
    for i in range(10):
        fake_counter.add_event(make_event(time_offset_sec=-400 + i, base_time=base_time))

    # Add 2 events inside the window
    for i in range(2):
        fake_counter.add_event(make_event(time_offset_sec=-10 + i, base_time=base_time))

    curr_event = make_event(time_offset_sec=0, base_time=base_time)
    # Total in window is only 2 -> no alert
    assert rule.evaluate(curr_event, fake_counter) is None


def test_brute_force_interleaved_ips(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(brute_force_threshold=5, brute_force_window_seconds=300)
    rule = BruteForceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    ip_a = "192.168.1.10"
    ip_b = "192.168.1.20"

    # 4 failures for IP A, 6 failures for IP B interleaved
    for i in range(4):
        fake_counter.add_event(make_event(ip=ip_a, time_offset_sec=-50 + i, base_time=base_time))
    for i in range(6):
        fake_counter.add_event(make_event(ip=ip_b, time_offset_sec=-50 + i, base_time=base_time))

    event_a = make_event(ip=ip_a, time_offset_sec=0, base_time=base_time)
    event_b = make_event(ip=ip_b, time_offset_sec=0, base_time=base_time)

    # IP A has 4 <= 5 -> No alert
    assert rule.evaluate(event_a, fake_counter) is None
    # IP B has 6 > 5 -> Alert!
    result_b = rule.evaluate(event_b, fake_counter)
    assert result_b is not None
    assert result_b.source_ip == ip_b
    assert result_b.dedup_key == f"BRUTE_FORCE:{ip_b}"


def test_brute_force_severity_bump_on_login_success(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(brute_force_threshold=10, brute_force_window_seconds=300)
    rule = BruteForceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ip = "203.0.113.10"

    # 12 failures (1.2 ratio -> base severity is LOW)
    for i in range(12):
        fake_counter.add_event(make_event(ip=ip, time_offset_sec=-100 + i, base_time=base_time))

    # Add a login success (200 OK) in the same window
    fake_counter.add_event(
        make_event(ip=ip, status_code=200, time_offset_sec=-10, base_time=base_time)
    )

    curr_event = make_event(ip=ip, time_offset_sec=0, base_time=base_time)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    # Base ratio 12/10 = 1.2 is LOW, but presence of login success bumps to MEDIUM!
    assert result.severity == Severity.MEDIUM
    assert result.evidence["login_success_after_failures"] is True
