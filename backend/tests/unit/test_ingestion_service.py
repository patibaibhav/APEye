"""Unit tests for IngestionService using fake repositories and mock sessions."""

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from app.core.config import Settings
from app.detection.detection_settings import DetectionSettings
from app.detection.engine import DetectionEngine
from app.detection.interfaces import WindowCounter
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, EndpointProfile, RequestEvent
from app.services.ingestion_service import IngestionService
from tests.unit.detection.test_alert_service import FakeAlertRepository


class FakeSession:
    """Mock database session tracking commit, rollback, and closed states."""

    def __init__(self) -> None:
        self.committed: int = 0
        self.rolled_back: int = 0
        self.closed: bool = False

    def commit(self) -> None:
        self.committed += 1

    def rollback(self) -> None:
        self.rolled_back += 1

    def close(self) -> None:
        self.closed = True


class FakeLogRepository:
    """Mock request log repository."""

    def __init__(self) -> None:
        self.stored_logs: List[RequestEvent] = []
        self.should_fail: bool = False

    def create_request_log(self, session: Any, event: RequestEvent) -> None:
        if self.should_fail:
            raise RuntimeError("Database connection lost during log write")
        self.stored_logs.append(event)


class DummyWindowCounter(WindowCounter):
    def count_requests(self, *, source_ip: str, start: datetime, end: datetime) -> int:
        return 1

    def count_by_status(
        self, *, statuses, start, end, source_ip=None, user_id=None, exclude_path=None
    ) -> int:
        return 0

    def count_login_failures(self, *, source_ip, login_path, start, end) -> int:
        return 0

    def has_login_success(self, *, source_ip, login_path, start, end) -> bool:
        return False

    def endpoint_profile(self, *, source_ip, start, end) -> EndpointProfile:
        return EndpointProfile(total_requests=1, distinct_paths=1, error_count=0, top_paths=[])


class DummyRule:
    category = ThreatCategory.EXCESSIVE_REQUESTS

    def __init__(self, will_trigger: bool = True, will_raise: bool = False) -> None:
        self.will_trigger = will_trigger
        self.will_raise = will_raise

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        if self.will_raise:
            raise RuntimeError("Rule crashed during evaluation")
        if not self.will_trigger:
            return None
        return DetectionResult(
            category=self.category,
            severity="LOW",  # type: ignore
            source_ip=event.source_ip,
            request_count=101,
            window_seconds=60,
            threshold=100,
            dedup_key=f"EXCESSIVE_REQUESTS:{event.source_ip}",
            detected_at=event.occurred_at,
        )


def make_test_event(ip: str = "203.0.113.10") -> RequestEvent:
    return RequestEvent(
        request_id=str(uuid.uuid4()),
        occurred_at=datetime.now(timezone.utc),
        source_ip=ip,
        path="/api/users",
        normalized_path="/api/users",
        method="GET",
        status_code=200,
        response_time_ms=20,
    )


def test_ingestion_successful_flow():
    session = FakeSession()
    log_repo = FakeLogRepository()
    alert_repo = FakeAlertRepository()
    engine = DetectionEngine(rules=[DummyRule(will_trigger=True)])

    service = IngestionService(
        session_factory=lambda: session,
        engine=engine,
        log_repo=log_repo,
        alert_repo=alert_repo,
        counter_factory=lambda sess: DummyWindowCounter(),
    )

    event = make_test_event()
    service.ingest(event)

    # 1. Log was stored and committed
    assert len(log_repo.stored_logs) == 1
    assert log_repo.stored_logs[0].request_id == event.request_id

    # 2. Alert was created and committed
    assert len(alert_repo.alerts) == 1
    # 2 commits: 1 for log, 1 for alert
    assert session.committed == 2
    assert session.rolled_back == 0
    assert session.closed is True


def test_ingestion_log_write_failure_stops_detection():
    session = FakeSession()
    log_repo = FakeLogRepository()
    log_repo.should_fail = True  # Simulate DB failure on log write
    alert_repo = FakeAlertRepository()
    engine = DetectionEngine(rules=[DummyRule(will_trigger=True)])

    service = IngestionService(
        session_factory=lambda: session,
        engine=engine,
        log_repo=log_repo,
        alert_repo=alert_repo,
        counter_factory=lambda sess: DummyWindowCounter(),
    )

    event = make_test_event()
    service.ingest(event)

    # Log failed -> session rolled back
    assert session.rolled_back == 1
    # Detection should not have run, no alerts created
    assert len(alert_repo.alerts) == 0
    assert session.closed is True


def test_ingestion_ignored_ips_skips_detection():
    session = FakeSession()
    log_repo = FakeLogRepository()
    alert_repo = FakeAlertRepository()
    engine = DetectionEngine(rules=[DummyRule(will_trigger=True)])

    # Configure ignored IPs
    detection_settings = DetectionSettings(ignore_ips=["127.0.0.1", "10.0.0.99"])
    settings = Settings(detection=detection_settings)

    service = IngestionService(
        session_factory=lambda: session,
        engine=engine,
        settings=settings,
        log_repo=log_repo,
        alert_repo=alert_repo,
        counter_factory=lambda sess: DummyWindowCounter(),
    )

    # Event from ignored IP
    event = make_test_event(ip="10.0.0.99")
    service.ingest(event)

    # Log was still stored!
    assert len(log_repo.stored_logs) == 1
    # But detection was skipped -> 0 alerts created
    assert len(alert_repo.alerts) == 0
    assert session.committed == 1  # only 1 commit for the log
    assert session.closed is True


def test_ingestion_detection_failure_keeps_stored_log():
    session = FakeSession()
    log_repo = FakeLogRepository()

    def exploding_counter_factory(sess):
        raise RuntimeError("Database error during window query")

    engine = DetectionEngine(rules=[DummyRule(will_trigger=True)])
    service = IngestionService(
        session_factory=lambda: session,
        engine=engine,
        log_repo=log_repo,
        alert_repo=FakeAlertRepository(),
        counter_factory=exploding_counter_factory,
    )

    event = make_test_event()
    service.ingest(event)

    # 1. Stored log remains committed!
    assert len(log_repo.stored_logs) == 1
    # 2. Detection failure caused rollback on detection transaction
    assert session.committed == 1  # 1 commit for the log
    assert session.rolled_back == 1  # 1 rollback for the detection phase
    assert session.closed is True
