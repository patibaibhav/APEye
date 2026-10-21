"""Unit tests for Rule C: Reconnaissance / Scanning Detection."""

from datetime import datetime, timedelta, timezone
import uuid

from app.detection.detection_settings import DetectionSettings
from app.detection.rules.reconnaissance import ReconnaissanceRule
from app.schemas.common import Severity, ThreatCategory
from app.schemas.detection import RequestEvent
from tests.unit.detection.conftest import FakeWindowCounter


def make_event(
    ip: str = "192.0.2.100",
    path: str = "/api/v1/unknown",
    status_code: int = 404,
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
        response_time_ms=15,
    )


def test_reconnaissance_trigger_guard(fake_counter: FakeWindowCounter):
    rule = ReconnaissanceRule()

    # 200 OK should not trigger
    assert rule.evaluate(make_event(status_code=200), fake_counter) is None
    # 500 error should not trigger (only 4xx)
    assert rule.evaluate(make_event(status_code=500), fake_counter) is None


def test_reconnaissance_all_three_conditions_required(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(
        recon_min_distinct=15,
        recon_min_requests=20,
        recon_min_error_ratio=0.5,
        recon_window_seconds=120,
    )
    rule = ReconnaissanceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ip = "192.0.2.100"

    # Case 1: distinct < 15, but total >= 20 and ratio >= 0.5
    counter_fail_distinct = FakeWindowCounter()
    for i in range(20):
        # Only 5 distinct paths
        counter_fail_distinct.add_event(
            make_event(ip=ip, path=f"/api/item/{i % 5}", status_code=404, time_offset_sec=-50 + i, base_time=base_time)
        )
    curr_event = make_event(ip=ip, path="/api/item/0", status_code=404, time_offset_sec=0, base_time=base_time)
    assert rule.evaluate(curr_event, counter_fail_distinct) is None

    # Case 2: distinct >= 15, ratio >= 0.5, but total < 20
    counter_fail_total = FakeWindowCounter()
    for i in range(16):  # Only 16 requests
        counter_fail_total.add_event(
            make_event(ip=ip, path=f"/api/path_{i}", status_code=404, time_offset_sec=-50 + i, base_time=base_time)
        )
    assert rule.evaluate(curr_event, counter_fail_total) is None

    # Case 3: distinct >= 15, total >= 20, but error ratio < 0.5
    counter_fail_ratio = FakeWindowCounter()
    for i in range(15):
        counter_fail_ratio.add_event(
            make_event(ip=ip, path=f"/api/err_{i}", status_code=404, time_offset_sec=-80 + i, base_time=base_time)
        )
    for i in range(20):
        counter_fail_ratio.add_event(
            make_event(ip=ip, path=f"/api/ok_{i}", status_code=200, time_offset_sec=-50 + i, base_time=base_time)
        )
    # Total = 35, errors = 15 -> ratio = 15/35 = 0.428 < 0.5
    assert rule.evaluate(curr_event, counter_fail_ratio) is None

    # Case 4: All 3 conditions met!
    counter_success = FakeWindowCounter()
    for i in range(20):
        counter_success.add_event(
            make_event(ip=ip, path=f"/api/probe_{i}", status_code=404, time_offset_sec=-60 + i, base_time=base_time)
        )
    result = rule.evaluate(curr_event, counter_success)
    assert result is not None
    assert result.category == ThreatCategory.RECONNAISSANCE
    assert result.dedup_key == f"RECONNAISSANCE:{ip}"
    assert result.evidence["distinct_count"] == 20
    assert result.evidence["error_ratio"] == 1.0


def test_reconnaissance_sensitive_patterns_bump(fake_counter: FakeWindowCounter):
    settings = DetectionSettings(
        recon_min_distinct=15,
        recon_min_requests=20,
        recon_min_error_ratio=0.5,
        recon_window_seconds=120,
        recon_sensitive_patterns=["/admin", "/.env", "/.git", "/config", "/backup"],
    )
    rule = ReconnaissanceRule(settings=settings)
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ip = "192.0.2.100"

    # 15 distinct paths (ratio = 15/15 = 1.0 -> LOW base severity)
    # Include 3 sensitive patterns: /admin, /.env, /.git
    sensitive_paths = ["/admin/login", "/.env", "/.git/config"]
    for i, sp in enumerate(sensitive_paths):
        fake_counter.add_event(make_event(ip=ip, path=sp, status_code=404, time_offset_sec=-60 + i, base_time=base_time))

    for i in range(17):
        fake_counter.add_event(
            make_event(ip=ip, path=f"/api/dummy_{i}", status_code=404, time_offset_sec=-40 + i, base_time=base_time)
        )

    curr_event = make_event(ip=ip, path="/.git/config", status_code=404, time_offset_sec=0, base_time=base_time)
    result = rule.evaluate(curr_event, fake_counter)
    assert result is not None
    # 3 sensitive patterns hit -> bumps from LOW to MEDIUM!
    assert result.severity == Severity.MEDIUM
    assert len(result.evidence["sensitive_pattern_hits"]) >= 3
