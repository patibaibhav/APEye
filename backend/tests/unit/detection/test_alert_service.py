"""Unit tests for alert_service: deduplication, cooldown, auto-close, transitions, notes."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest

from app.core.errors import AlertNotFoundError, InvalidTransitionError, ValidationError
from app.schemas.alerts import AlertDetail, AlertNoteRead
from app.schemas.common import AlertStatus, Severity, ThreatCategory
from app.schemas.detection import DetectionResult
from app.services.alert_service import (
    add_note,
    change_status,
    process_results,
)


class FakeAlertRepository:
    """In-memory alert repository fake for testing alert_service logic."""

    def __init__(self) -> None:
        self.alerts: Dict[int, AlertDetail] = {}
        self.next_id: int = 1
        self.next_note_id: int = 1
        self.simulate_integrity_error: bool = False

    def find_open_by_dedup_key(self, session: Any, dedup_key: str) -> Optional[AlertDetail]:
        for alert in self.alerts.values():
            if alert.dedup_key == dedup_key and alert.status in (
                AlertStatus.ACTIVE,
                AlertStatus.INVESTIGATING,
            ):
                return alert
        return None

    def get_alert_by_id(self, session: Any, alert_id: int) -> Optional[AlertDetail]:
        return self.alerts.get(alert_id)

    def create_alert(self, session: Any, result: DetectionResult) -> AlertDetail:
        if self.simulate_integrity_error:
            self.simulate_integrity_error = False
            raise RuntimeError("IntegrityError: partial unique index conflict on dedup_key")

        alert = AlertDetail(
            id=self.next_id,
            category=result.category,
            severity=result.severity,
            status=AlertStatus.ACTIVE,
            source_ip=result.source_ip,
            user_id=result.user_id,
            endpoints=result.endpoints,
            request_count=result.request_count,
            window_seconds=result.window_seconds,
            threshold=result.threshold,
            event_count=1,
            first_detected_at=result.detected_at,
            last_detected_at=result.detected_at,
            evidence=result.evidence,
            notes=[],
        )
        # Store dedup_key dynamically on the alert object
        setattr(alert, "dedup_key", result.dedup_key)
        self.alerts[self.next_id] = alert
        self.next_id += 1
        return alert

    def touch_alert(
        self,
        session: Any,
        alert: AlertDetail,
        last_detected_at: datetime,
        event_count: int,
        evidence: Dict[str, Any],
        request_count: int,
        endpoints: List[str],
        severity: Severity,
    ) -> AlertDetail:
        alert.last_detected_at = last_detected_at
        alert.event_count = event_count
        alert.evidence = evidence
        alert.request_count = request_count
        alert.endpoints = endpoints
        alert.severity = severity
        return alert

    def set_status(
        self,
        session: Any,
        alert: AlertDetail,
        status: AlertStatus,
        actor_id: Optional[int],
        resolved_at: Optional[datetime],
    ) -> AlertDetail:
        alert.status = status
        alert.resolved_at = resolved_at
        alert.updated_by = actor_id
        return alert

    def add_note(
        self,
        session: Any,
        alert_id: int,
        author_id: Optional[int],
        note: str,
        created_at: datetime,
    ) -> AlertNoteRead:
        alert = self.alerts[alert_id]
        note_obj = AlertNoteRead(
            id=self.next_note_id,
            alert_id=alert_id,
            author_id=author_id,
            author_username="analyst" if author_id else None,
            note=note,
            created_at=created_at,
        )
        self.next_note_id += 1
        alert.notes.append(note_obj)
        return note_obj


def make_result(
    category: ThreatCategory = ThreatCategory.BRUTE_FORCE,
    severity: Severity = Severity.LOW,
    ip: str = "203.0.113.10",
    dedup_key: str = "BRUTE_FORCE:203.0.113.10",
    detected_at: Optional[datetime] = None,
) -> DetectionResult:
    now = detected_at or datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return DetectionResult(
        category=category,
        severity=severity,
        source_ip=ip,
        endpoints=["/api/auth/login"],
        request_count=11,
        window_seconds=300,
        threshold=10,
        evidence={"count": 11},
        dedup_key=dedup_key,
        detected_at=now,
    )


def test_process_results_creates_new_alert():
    repo = FakeAlertRepository()
    result = make_result()

    outcomes = process_results("fake_session", [result], cooldown_seconds=600, alert_repo=repo)

    assert len(outcomes) == 1
    assert outcomes[0].action == "created"
    assert outcomes[0].alert_id == 1

    alert = repo.alerts[1]
    assert alert.status == AlertStatus.ACTIVE
    assert alert.event_count == 1
    assert alert.severity == Severity.LOW


def test_process_results_updates_existing_within_cooldown():
    repo = FakeAlertRepository()
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    r1 = make_result(severity=Severity.LOW, detected_at=t0)
    process_results("fake_session", [r1], cooldown_seconds=600, alert_repo=repo)

    # Second result arrives 120 seconds later (within 600s cooldown) with higher severity MEDIUM
    t1 = t0 + timedelta(seconds=120)
    r2 = make_result(severity=Severity.MEDIUM, detected_at=t1)
    outcomes = process_results("fake_session", [r2], cooldown_seconds=600, alert_repo=repo)

    assert len(outcomes) == 1
    assert outcomes[0].action == "updated"
    assert outcomes[0].alert_id == 1

    alert = repo.alerts[1]
    assert alert.event_count == 2
    assert alert.last_detected_at == t1
    assert alert.severity == Severity.MEDIUM


def test_process_results_severity_never_lowers():
    repo = FakeAlertRepository()
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    # Existing alert is HIGH
    r1 = make_result(severity=Severity.HIGH, detected_at=t0)
    process_results("fake_session", [r1], cooldown_seconds=600, alert_repo=repo)

    # Second result has LOW severity
    t1 = t0 + timedelta(seconds=60)
    r2 = make_result(severity=Severity.LOW, detected_at=t1)
    process_results("fake_session", [r2], cooldown_seconds=600, alert_repo=repo)

    alert = repo.alerts[1]
    # Severity must remain HIGH!
    assert alert.severity == Severity.HIGH


def test_process_results_stale_active_auto_closes_and_creates_new():
    repo = FakeAlertRepository()
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    r1 = make_result(detected_at=t0)
    process_results("fake_session", [r1], cooldown_seconds=600, alert_repo=repo)

    # Next result arrives 700 seconds later (> 600s cooldown)
    t1 = t0 + timedelta(seconds=700)
    r2 = make_result(detected_at=t1)
    outcomes = process_results("fake_session", [r2], cooldown_seconds=600, alert_repo=repo)

    assert len(outcomes) == 1
    assert outcomes[0].action == "auto_closed_and_created"
    assert outcomes[0].alert_id == 2  # New alert ID

    # Old alert is RESOLVED with system note
    old_alert = repo.alerts[1]
    assert old_alert.status == AlertStatus.RESOLVED
    assert len(old_alert.notes) == 1
    assert old_alert.notes[0].note == "auto-closed: inactive beyond cooldown"
    assert old_alert.notes[0].author_id is None

    # New alert is ACTIVE with 1 event
    new_alert = repo.alerts[2]
    assert new_alert.status == AlertStatus.ACTIVE
    assert new_alert.event_count == 1
    assert new_alert.first_detected_at == t1


def test_process_results_investigating_never_auto_closed():
    repo = FakeAlertRepository()
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    r1 = make_result(detected_at=t0)
    process_results("fake_session", [r1], cooldown_seconds=600, alert_repo=repo)

    # Analyst marks alert INVESTIGATING
    repo.alerts[1].status = AlertStatus.INVESTIGATING

    # Result arrives 1000s later (way beyond cooldown)
    t1 = t0 + timedelta(seconds=1000)
    r2 = make_result(detected_at=t1)
    outcomes = process_results("fake_session", [r2], cooldown_seconds=600, alert_repo=repo)

    assert len(outcomes) == 1
    assert outcomes[0].action == "updated"
    assert outcomes[0].alert_id == 1

    # Stays INVESTIGATING; must never be auto-closed
    alert = repo.alerts[1]
    assert alert.status == AlertStatus.INVESTIGATING
    assert alert.event_count == 2


def test_process_results_concurrency_race_condition():
    repo = FakeAlertRepository()
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    r1 = make_result(detected_at=t0)

    # First worker creates alert 1
    repo.create_alert("fake_session", r1)

    # Second concurrent worker tries creating and hits simulated IntegrityError
    repo.simulate_integrity_error = True
    outcomes = process_results("fake_session", [r1], cooldown_seconds=600, alert_repo=repo)

    assert len(outcomes) == 1
    assert outcomes[0].action == "updated"
    assert outcomes[0].alert_id == 1


def test_change_status_allowed_and_forbidden_transitions():
    repo = FakeAlertRepository()
    result = make_result()
    process_results("fake_session", [result], alert_repo=repo)

    # 1. ACTIVE -> INVESTIGATING is allowed
    updated = change_status(
        "fake_session", 1, AlertStatus.INVESTIGATING, actor_id=99, alert_repo=repo
    )
    assert updated.status == AlertStatus.INVESTIGATING

    # 2. INVESTIGATING -> RESOLVED is allowed
    updated = change_status("fake_session", 1, AlertStatus.RESOLVED, actor_id=99, alert_repo=repo)
    assert updated.status == AlertStatus.RESOLVED
    assert updated.resolved_at is not None

    # 3. RESOLVED -> ACTIVE (reopen) is allowed
    updated = change_status("fake_session", 1, AlertStatus.ACTIVE, actor_id=99, alert_repo=repo)
    assert updated.status == AlertStatus.ACTIVE
    assert updated.resolved_at is None

    # 4. ACTIVE -> ACTIVE is forbidden (409 InvalidTransition)
    with pytest.raises(InvalidTransitionError):
        change_status("fake_session", 1, AlertStatus.ACTIVE, actor_id=99, alert_repo=repo)

    # 5. Non-existent alert raises AlertNotFoundError (404)
    with pytest.raises(AlertNotFoundError):
        change_status("fake_session", 999, AlertStatus.RESOLVED, actor_id=99, alert_repo=repo)


def test_add_note_validation_and_author():
    repo = FakeAlertRepository()
    result = make_result()
    process_results("fake_session", [result], alert_repo=repo)

    # Valid analyst note
    note = add_note("fake_session", 1, author_id=5, note="Investigating IP range.", alert_repo=repo)
    assert note.id == 1
    assert note.author_id == 5
    assert note.note == "Investigating IP range."
    assert len(repo.alerts[1].notes) == 1

    # Empty note raises ValidationError (422)
    with pytest.raises(ValidationError):
        add_note("fake_session", 1, author_id=5, note="   ", alert_repo=repo)

    # Note exceeding 2000 chars raises ValidationError
    with pytest.raises(ValidationError):
        add_note("fake_session", 1, author_id=5, note="A" * 2001, alert_repo=repo)

    # Note on non-existent alert raises AlertNotFoundError
    with pytest.raises(AlertNotFoundError):
        add_note("fake_session", 999, author_id=5, note="Hello", alert_repo=repo)
