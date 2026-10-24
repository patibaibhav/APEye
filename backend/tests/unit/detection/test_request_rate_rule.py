"""Unit tests for Rule B: Request Rate (Excessive Requests) Detection."""

import uuid
from datetime import datetime, timedelta, timezone

from app.detection.detection_settings import DetectionSettings
from app.detection.rules.request_rate import RequestRateRule
from app.schemas.common import Severity, ThreatCategory
from app.schemas.detection import RequestEvent
from tests.unit.detection.conftest import FakeWindowCounter


def make_event(
    ip: str = "198.51.100.5",
    path: str = "/api/dashboard",
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
        status_code=200,
        response_time_ms=10,
    )


def test_request_rate_threshold_boundaries(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(rate_threshold=100, rate_window_seconds=60)
    rule = RequestRateRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Exactly 100 events
    for i in range(100):
        fake_counter.add_event(make_event(time_offset_sec=-50 + (i % 50), base_time=base_time))

    curr_event = make_event(time_offset_sec=0, base_time=base_time)
    # Exactly at threshold 100 -> NO alert
    assert rule.evaluate(curr_event, fake_counter) is None

    # Add 1 more event -> 101 (threshold plus one)
    fake_counter.add_event(curr_event)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    assert result.category == ThreatCategory.EXCESSIVE_REQUESTS
    assert result.request_count == 101
    assert result.threshold == 100
    assert result.severity == Severity.LOW
    assert result.dedup_key == "EXCESSIVE_REQUESTS:198.51.100.5"


def test_request_rate_events_outside_window(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(rate_threshold=100, rate_window_seconds=60)
    rule = RequestRateRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # 150 events that happened 120s ago (outside 60s window)
    for i in range(150):
        fake_counter.add_event(make_event(time_offset_sec=-120 + (i % 10), base_time=base_time))

    curr_event = make_event(time_offset_sec=0, base_time=base_time)
    assert rule.evaluate(curr_event, fake_counter) is None


def test_request_rate_interleaved_ips(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(rate_threshold=50, rate_window_seconds=60)
    rule = RequestRateRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    ip_low = "10.0.0.1"
    ip_high = "10.0.0.2"

    for i in range(30):
        fake_counter.add_event(make_event(ip=ip_low, time_offset_sec=-30 + i, base_time=base_time))
    for i in range(60):
        fake_counter.add_event(
            make_event(ip=ip_high, time_offset_sec=-30 + (i % 30), base_time=base_time)
        )

    event_low = make_event(ip=ip_low, time_offset_sec=0, base_time=base_time)
    event_high = make_event(ip=ip_high, time_offset_sec=0, base_time=base_time)

    assert rule.evaluate(event_low, fake_counter) is None
    result_high = rule.evaluate(event_high, fake_counter)
    assert result_high is not None
    assert result_high.source_ip == ip_high
    assert result_high.dedup_key == f"EXCESSIVE_REQUESTS:{ip_high}"


def test_request_rate_severity_levels(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(rate_threshold=100, rate_window_seconds=60)
    rule = RequestRateRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ip = "198.51.100.99"

    # Seed 170 events -> ratio 1.7 -> MEDIUM
    for i in range(170):
        fake_counter.add_event(
            make_event(ip=ip, time_offset_sec=-40 + (i % 40), base_time=base_time)
        )

    curr_event = make_event(ip=ip, time_offset_sec=0, base_time=base_time)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    assert result.severity == Severity.MEDIUM

    # Add 150 more -> 320 events total -> ratio 3.2 -> HIGH
    for i in range(150):
        fake_counter.add_event(
            make_event(ip=ip, time_offset_sec=-40 + (i % 40), base_time=base_time)
        )

    result_high = rule.evaluate(curr_event, fake_counter)
    assert result_high is not None
    assert result_high.severity == Severity.HIGH
