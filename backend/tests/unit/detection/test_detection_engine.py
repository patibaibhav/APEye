"""Unit tests for DetectionEngine: rule ordering, multiple alerts, and failure isolation."""

import uuid
from datetime import datetime, timezone

from app.detection.engine import DetectionEngine, build_default_engine
from app.detection.interfaces import WindowCounter
from app.detection.rules.brute_force import BruteForceRule
from app.detection.rules.reconnaissance import ReconnaissanceRule
from app.detection.rules.request_rate import RequestRateRule
from app.detection.rules.unauthorized_access import UnauthorizedAccessRule
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, RequestEvent
from tests.unit.detection.conftest import FakeWindowCounter


def make_event(
    ip: str = "203.0.113.88",
    path: str = "/api/auth/login",
    status_code: int = 401,
    method: str = "POST",
) -> RequestEvent:
    return RequestEvent(
        request_id=str(uuid.uuid4()),
        occurred_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        source_ip=ip,
        path=path,
        normalized_path=path,
        method=method,
        status_code=status_code,
        response_time_ms=30,
    )


class ExplodingRule:
    """A faulty rule that always raises an unhandled exception."""

    category = ThreatCategory.BRUTE_FORCE

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> DetectionResult | None:
        raise ZeroDivisionError("Simulated bug inside rule code")


class AlwaysAlertRule:
    """A mock rule that always returns a detection result."""

    def __init__(self, category: ThreatCategory) -> None:
        self.category = category

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> DetectionResult | None:
        return DetectionResult(
            category=self.category,
            severity="LOW",  # type: ignore
            source_ip=event.source_ip,
            request_count=1,
            window_seconds=60,
            threshold=0,
            dedup_key=f"{self.category.value}:{event.source_ip}",
            detected_at=event.occurred_at,
        )


def test_default_engine_rule_order():
    engine = build_default_engine()
    assert len(engine.rules) == 4
    # Expected order: A (Brute Force), B (Request Rate), D (Unauthorized Access), C (Reconnaissance)
    assert isinstance(engine.rules[0], BruteForceRule)
    assert isinstance(engine.rules[1], RequestRateRule)
    assert isinstance(engine.rules[2], UnauthorizedAccessRule)
    assert isinstance(engine.rules[3], ReconnaissanceRule)


def test_engine_rule_failure_isolation(fake_counter: FakeWindowCounter):
    # Setup an engine where the first rule crashes, but the second rule succeeds
    engine = DetectionEngine(
        rules=[
            ExplodingRule(),
            AlwaysAlertRule(ThreatCategory.EXCESSIVE_REQUESTS),
        ]
    )

    event = make_event()
    results = engine.evaluate(event, fake_counter)

    # The exploding rule must NOT crash the engine or block the subsequent rule!
    assert len(results) == 1
    assert results[0].category == ThreatCategory.EXCESSIVE_REQUESTS
    assert engine.error_count == 1


def test_engine_counter_failure_isolation(fake_counter: FakeWindowCounter):
    # Configure the fake counter to raise on database query
    fake_counter.should_raise = True
    engine = build_default_engine()

    event = make_event()
    # Must not raise an exception; must return empty results and increment error count
    results = engine.evaluate(event, fake_counter)
    assert results == []
    assert engine.error_count > 0


def test_engine_multiple_alerts_for_single_event(fake_counter: FakeWindowCounter):
    # When multiple rules trigger on the same event, all must be collected
    engine = DetectionEngine(
        rules=[
            AlwaysAlertRule(ThreatCategory.BRUTE_FORCE),
            AlwaysAlertRule(ThreatCategory.EXCESSIVE_REQUESTS),
        ]
    )

    event = make_event()
    results = engine.evaluate(event, fake_counter)
    assert len(results) == 2
    assert results[0].category == ThreatCategory.BRUTE_FORCE
    assert results[1].category == ThreatCategory.EXCESSIVE_REQUESTS
