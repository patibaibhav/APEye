"""IP Investigation repository and derived suspicious IP aggregation (Owner: Anvi).

Implements:
- Derived alert-grouped view of suspicious IPs
- CRUD on ip_investigations table
- Supports GET /api/suspicious-ips, GET /api/suspicious-ips/{ip}, and PATCH /api/suspicious-ips/{ip}/investigation
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert import Alert
from app.db.models.investigation import IpInvestigation
from app.schemas.alerts import AlertListItem
from app.schemas.common import AlertStatus, Severity, ThreatCategory
from app.schemas.suspicious_ips import InvestigationStatus, SuspiciousIpDetail, SuspiciousIpListItem


def get_investigation(session: Session, source_ip: str) -> Optional[IpInvestigation]:
    """Retrieves an IP investigation record by source_ip."""
    stmt = select(IpInvestigation).where(IpInvestigation.source_ip == source_ip)
    return session.execute(stmt).scalar_one_or_none()


def upsert_investigation(
    session: Session,
    source_ip: str,
    status: InvestigationStatus,
    note: Optional[str] = None,
    updated_by: Optional[int] = None,
) -> IpInvestigation:
    """Creates or updates an IP investigation status and note."""
    status_val = status.value if hasattr(status, "value") else str(status)
    inv = get_investigation(session, source_ip)
    if inv is None:
        inv = IpInvestigation(
            source_ip=source_ip,
            status=status_val,
            note=note,
            updated_by=updated_by,
            updated_at=datetime.now(timezone.utc),
        )
        session.add(inv)
    else:
        inv.status = status_val
        if note is not None:
            inv.note = note
        inv.updated_by = updated_by
        inv.updated_at = datetime.now(timezone.utc)

    session.flush()
    return inv


def get_suspicious_ip_summary(
    session: Session,
    source_ip: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Optional[SuspiciousIpListItem]:
    """Builds a SuspiciousIpListItem summary for a specific source IP from its alerts."""
    stmt = select(Alert).where(Alert.source_ip == source_ip)
    if start:
        stmt = stmt.where(Alert.first_detected_at >= start)
    if end:
        stmt = stmt.where(Alert.first_detected_at < end)
    stmt = stmt.order_by(Alert.last_detected_at.desc())

    alerts = list(session.execute(stmt).scalars().all())
    if not alerts:
        # If no alerts in the window, check if any alerts exist at all for this IP
        all_stmt = (
            select(Alert)
            .where(Alert.source_ip == source_ip)
            .order_by(Alert.last_detected_at.desc())
        )
        alerts = list(session.execute(all_stmt).scalars().all())
        if not alerts:
            return None

    inv = get_investigation(session, source_ip)
    inv_status = InvestigationStatus(inv.status) if inv else InvestigationStatus.NEW
    inv_note = inv.note if inv else None

    categories = list({ThreatCategory(a.category) for a in alerts})
    total_req_count = sum(a.request_count for a in alerts)
    open_count = sum(1 for a in alerts if a.status in ("ACTIVE", "INVESTIGATING"))
    latest = max(a.last_detected_at for a in alerts)
    related_ids = [a.id for a in alerts]

    return SuspiciousIpListItem(
        source_ip=source_ip,
        suspicious_request_count=total_req_count,
        categories=categories,
        latest_activity=latest,
        alert_count=len(alerts),
        open_alert_count=open_count,
        related_alert_ids=related_ids,
        investigation_status=inv_status,
        investigation_note=inv_note,
    )


def list_suspicious_ips(
    session: Session,
    investigation_status: Optional[InvestigationStatus] = None,
    category: Optional[ThreatCategory] = None,
    source_ip: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 25,
) -> Tuple[List[SuspiciousIpListItem], int]:
    """Lists aggregated suspicious IPs derived from alerts, with pagination and filtering."""
    # Find distinct source_ips having alerts matching the criteria
    base_stmt = select(Alert.source_ip).distinct()
    if source_ip:
        base_stmt = base_stmt.where(Alert.source_ip == source_ip)
    if category:
        cat_val = category.value if hasattr(category, "value") else str(category)
        base_stmt = base_stmt.where(Alert.category == cat_val)
    if start:
        base_stmt = base_stmt.where(Alert.first_detected_at >= start)
    if end:
        base_stmt = base_stmt.where(Alert.first_detected_at < end)

    candidate_ips = list(session.execute(base_stmt).scalars().all())

    # Build summaries and filter by investigation_status if specified
    summaries: List[SuspiciousIpListItem] = []
    for ip in candidate_ips:
        summary = get_suspicious_ip_summary(session, ip, start=start, end=end)
        if summary:
            if investigation_status is not None:
                if summary.investigation_status != investigation_status:
                    continue
            summaries.append(summary)

    # Sort by latest_activity descending
    summaries.sort(key=lambda s: s.latest_activity, reverse=True)
    total = len(summaries)
    paginated = summaries[offset : offset + limit]

    return paginated, total


def get_suspicious_ip_detail(
    session: Session,
    source_ip: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Optional[SuspiciousIpDetail]:
    """Builds SuspiciousIpDetail including all associated alerts."""
    summary = get_suspicious_ip_summary(session, source_ip, start=start, end=end)
    if summary is None:
        return None

    stmt = select(Alert).where(Alert.source_ip == source_ip)
    if start:
        stmt = stmt.where(Alert.first_detected_at >= start)
    if end:
        stmt = stmt.where(Alert.first_detected_at < end)
    stmt = stmt.order_by(Alert.last_detected_at.desc(), Alert.id.desc())

    alert_rows = list(session.execute(stmt).scalars().all())
    alerts_dto = [
        AlertListItem(
            id=a.id,
            category=ThreatCategory(a.category),
            severity=Severity(a.severity),
            status=AlertStatus(a.status),
            source_ip=a.source_ip,
            endpoints=a.endpoints or [],
            request_count=a.request_count,
            window_seconds=a.window_seconds,
            event_count=a.event_count,
            first_detected_at=a.first_detected_at,
            last_detected_at=a.last_detected_at,
        )
        for a in alert_rows
    ]

    return SuspiciousIpDetail(
        source_ip=summary.source_ip,
        suspicious_request_count=summary.suspicious_request_count,
        categories=summary.categories,
        latest_activity=summary.latest_activity,
        alert_count=summary.alert_count,
        open_alert_count=summary.open_alert_count,
        related_alert_ids=summary.related_alert_ids,
        investigation_status=summary.investigation_status,
        investigation_note=summary.investigation_note,
        alerts=alerts_dto,
    )
