"""Tests for SQLAlchemy database models, constraints, and cascade delete behavior (Owner: Anvi)."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.alert import Alert, AlertNote
from app.db.models.log import ApiRequestLog
from app.db.models.user import User
from app.db.session import SessionLocal


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_user_unique_username_constraint(db_session):
    u1 = User(
        username="unique_user_test",
        password_hash="hash1",
        role="ANALYST",
    )
    db_session.add(u1)
    db_session.commit()

    u2 = User(
        username="unique_user_test",
        password_hash="hash2",
        role="ADMIN",
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_role_check_constraint(db_session):
    invalid_user = User(
        username="invalid_role_user",
        password_hash="hash",
        role="SUPERUSER",  # Violates ck_users_role
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_api_request_logs_foreign_key_set_null(db_session):
    user = User(username="fk_test_user", password_hash="hash", role="ANALYST")
    db_session.add(user)
    db_session.commit()

    log = ApiRequestLog(
        request_id="test-fk-log-1",
        occurred_at=datetime.now(timezone.utc),
        source_ip="10.0.0.99",
        path="/api/test",
        normalized_path="/api/test",
        method="GET",
        status_code=200,
        response_time_ms=10,
        auth_outcome="AUTHENTICATED",
        user_id=user.id,
    )
    db_session.add(log)
    db_session.commit()

    # Delete the user; log's user_id must be SET NULL
    db_session.delete(user)
    db_session.commit()

    db_session.refresh(log)
    assert log.user_id is None


def test_alert_notes_cascade_delete(db_session):
    now = datetime.now(timezone.utc)
    alert = Alert(
        category="BRUTE_FORCE",
        severity="MEDIUM",
        status="ACTIVE",
        source_ip="192.0.2.99",
        dedup_key="CASCADE_TEST_ALERT",
        endpoints=["/login"],
        evidence={},
        request_count=5,
        window_seconds=60,
        threshold=5,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(alert)
    db_session.commit()

    note = AlertNote(
        alert_id=alert.id,
        author_id=None,
        note="Test cascade note",
        created_at=now,
    )
    db_session.add(note)
    db_session.commit()

    note_id = note.id
    # Delete the alert; note must be deleted automatically via CASCADE
    db_session.delete(alert)
    db_session.commit()

    fetched_note = db_session.execute(
        select(AlertNote).where(AlertNote.id == note_id)
    ).scalar_one_or_none()
    assert fetched_note is None


def test_alert_partial_unique_index_on_dedup_key(db_session):
    now = datetime.now(timezone.utc)
    a1 = Alert(
        category="RECONNAISSANCE",
        severity="LOW",
        status="ACTIVE",
        source_ip="198.51.100.99",
        dedup_key="PARTIAL_INDEX_TEST",
        endpoints=["/admin"],
        evidence={},
        request_count=1,
        window_seconds=60,
        threshold=1,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(a1)
    db_session.commit()

    # Adding another ACTIVE alert with same dedup_key must fail
    a2 = Alert(
        category="RECONNAISSANCE",
        severity="LOW",
        status="ACTIVE",
        source_ip="198.51.100.99",
        dedup_key="PARTIAL_INDEX_TEST",
        endpoints=["/admin"],
        evidence={},
        request_count=2,
        window_seconds=60,
        threshold=1,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(a2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # But once a1 is RESOLVED, creating a new ACTIVE alert with that dedup_key is allowed!
    db_session.refresh(a1)
    a1.status = "RESOLVED"
    db_session.commit()

    a3 = Alert(
        category="RECONNAISSANCE",
        severity="LOW",
        status="ACTIVE",
        source_ip="198.51.100.99",
        dedup_key="PARTIAL_INDEX_TEST",
        endpoints=["/admin"],
        evidence={},
        request_count=3,
        window_seconds=60,
        threshold=1,
        first_detected_at=now,
        last_detected_at=now,
    )
    db_session.add(a3)
    db_session.commit()
    assert a3.id is not None
