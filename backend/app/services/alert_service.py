"""Alert lifecycle service (Owner: Baibhav).

Implements deduplication, cooldown rules, state transitions, and notes.
Follows the Detection and API contracts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set

from pydantic import BaseModel

from app.core.errors import AlertNotFoundError, InvalidTransitionError, ValidationError
from app.core.logging_config import get_ops_logger
from app.schemas.alerts import AlertNoteRead, AlertRead
from app.schemas.common import AlertStatus, Severity
from app.schemas.detection import AlertOutcome, DetectionResult

ALLOWED_TRANSITIONS: Dict[AlertStatus, Set[AlertStatus]] = {
    AlertStatus.ACTIVE: {AlertStatus.INVESTIGATING, AlertStatus.RESOLVED},
    AlertStatus.INVESTIGATING: {AlertStatus.ACTIVE, AlertStatus.RESOLVED},
    AlertStatus.RESOLVED: {AlertStatus.ACTIVE},
}

_SEVERITY_RANK: Dict[Severity, int] = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
}


class AlertData(BaseModel):
    id: int
    category: Any
    severity: Severity
    status: AlertStatus
    source_ip: str
    user_id: Optional[int] = None
    dedup_key: str
    endpoints: List[str]
    evidence: Dict[str, Any]
    request_count: int
    window_seconds: int
    threshold: int
    event_count: int = 1
    first_detected_at: datetime
    last_detected_at: datetime
    resolved_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    notes: List[Any] = []


def _higher_severity(sev1: Severity, sev2: Severity) -> Severity:
    """Returns the higher of two severities; severity never lowers."""
    return sev2 if _SEVERITY_RANK.get(sev2, 0) > _SEVERITY_RANK.get(sev1, 0) else sev1


def process_results(
    session: Any,
    results: Sequence[DetectionResult],
    *,
    cooldown_seconds: int = 600,
    alert_repo: Any = None,
) -> List[AlertOutcome]:
    """Processes detection results against existing open alerts with deduplication and cooldown."""
    outcomes: List[AlertOutcome] = []
    ops_logger = get_ops_logger()

    # Fallback to importing alert_repository if not injected
    repo = alert_repo
    if repo is None:
        try:
            from app.db.repositories import alert_repository as repo
        except ImportError:
            # If Anvi's repository is not yet present, session itself acts as repo in tests
            repo = session

    for result in results:
        # 1. Look for existing open alert (ACTIVE or INVESTIGATING) with matching dedup_key
        open_alert = repo.find_open_by_dedup_key(session, result.dedup_key)

        if open_alert is not None:
            time_diff = (result.detected_at - open_alert.last_detected_at).total_seconds()
            is_active_inside_cooldown = (
                open_alert.status == AlertStatus.ACTIVE and time_diff <= cooldown_seconds
            )
            is_investigating = open_alert.status == AlertStatus.INVESTIGATING

            if is_investigating or is_active_inside_cooldown:
                # Update existing open alert
                new_severity = _higher_severity(open_alert.severity, result.severity)
                repo.touch_alert(
                    session,
                    alert=open_alert,
                    last_detected_at=result.detected_at,
                    event_count=open_alert.event_count + 1,
                    evidence=result.evidence,
                    request_count=result.request_count,
                    endpoints=result.endpoints,
                    severity=new_severity,
                )
                ops_logger.info(
                    "alert_updated",
                    extra={
                        "extra_fields": {
                            "alert_id": open_alert.id,
                            "category": str(open_alert.category),
                            "severity": str(new_severity),
                            "source_ip": open_alert.source_ip,
                        }
                    },
                )
                outcomes.append(AlertOutcome(action="updated", alert_id=open_alert.id))
            else:
                # ACTIVE alert is stale beyond cooldown -> auto-close and create new
                repo.set_status(
                    session,
                    alert=open_alert,
                    status=AlertStatus.RESOLVED,
                    actor_id=None,
                    resolved_at=result.detected_at,
                )
                repo.add_note(
                    session,
                    alert_id=open_alert.id,
                    author_id=None,
                    note="auto-closed: inactive beyond cooldown",
                    created_at=result.detected_at,
                )
                ops_logger.info(
                    "alert_auto_closed",
                    extra={
                        "extra_fields": {
                            "alert_id": open_alert.id,
                            "category": str(open_alert.category),
                            "source_ip": open_alert.source_ip,
                        }
                    },
                )

                # Create fresh ACTIVE alert
                new_alert = repo.create_alert(session, result)
                ops_logger.info(
                    "alert_created",
                    extra={
                        "extra_fields": {
                            "alert_id": new_alert.id,
                            "category": str(new_alert.category),
                            "severity": str(new_alert.severity),
                            "source_ip": new_alert.source_ip,
                        }
                    },
                )
                outcomes.append(
                    AlertOutcome(action="auto_closed_and_created", alert_id=new_alert.id)
                )

        else:
            # No open alert exists; create a new alert
            try:
                new_alert = repo.create_alert(session, result)
                ops_logger.info(
                    "alert_created",
                    extra={
                        "extra_fields": {
                            "alert_id": new_alert.id,
                            "category": str(new_alert.category),
                            "severity": str(new_alert.severity),
                            "source_ip": new_alert.source_ip,
                        }
                    },
                )
                outcomes.append(AlertOutcome(action="created", alert_id=new_alert.id))
            except Exception as exc:
                # Handle race condition: partial unique index conflict
                if "IntegrityError" in type(exc).__name__ or "unique" in str(exc).lower():
                    # Re-read and update once
                    concurrent_alert = repo.find_open_by_dedup_key(session, result.dedup_key)
                    if concurrent_alert is not None:
                        new_severity = _higher_severity(concurrent_alert.severity, result.severity)
                        repo.touch_alert(
                            session,
                            alert=concurrent_alert,
                            last_detected_at=result.detected_at,
                            event_count=concurrent_alert.event_count + 1,
                            evidence=result.evidence,
                            request_count=result.request_count,
                            endpoints=result.endpoints,
                            severity=new_severity,
                        )
                        outcomes.append(AlertOutcome(action="updated", alert_id=concurrent_alert.id))
                    else:
                        raise
                else:
                    raise

    return outcomes


def change_status(
    session: Any,
    alert_id: int,
    new_status: AlertStatus,
    actor_id: int,
    alert_repo: Any = None,
) -> AlertRead:
    """Transitions an alert's status if permitted by the frozen state machine."""
    repo = alert_repo
    if repo is None:
        try:
            from app.db.repositories import alert_repository as repo
        except ImportError:
            repo = session

    alert = repo.get_alert_by_id(session, alert_id)
    if alert is None:
        raise AlertNotFoundError(f"Alert with ID {alert_id} not found")

    current_status = AlertStatus(alert.status)
    target_status = AlertStatus(new_status)

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition alert from {current_status.value} to {target_status.value}"
        )

    resolved_at = datetime.now(timezone.utc) if target_status == AlertStatus.RESOLVED else None
    updated = repo.set_status(
        session,
        alert=alert,
        status=target_status,
        actor_id=actor_id,
        resolved_at=resolved_at,
    )
    return repo.get_alert_detail(session, alert_id) if hasattr(repo, "get_alert_detail") else updated


def add_note(
    session: Any,
    alert_id: int,
    author_id: Optional[int],
    note: str,
    alert_repo: Any = None,
) -> AlertNoteRead:
    """Attaches an analyst or system note to an alert."""
    if not (1 <= len(note.strip()) <= 2000):
        raise ValidationError("Note length must be between 1 and 2000 characters")

    repo = alert_repo
    if repo is None:
        try:
            from app.db.repositories import alert_repository as repo
        except ImportError:
            repo = session

    alert = repo.get_alert_by_id(session, alert_id)
    if alert is None:
        raise AlertNotFoundError(f"Alert with ID {alert_id} not found")

    created_note = repo.add_note(
        session,
        alert_id=alert_id,
        author_id=author_id,
        note=note.strip(),
        created_at=datetime.now(timezone.utc),
    )
    return created_note
