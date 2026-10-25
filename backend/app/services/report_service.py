"""Report service generating report content, compressing archives, and persisting metadata (Owner: Anvi)."""

import gzip
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.models.report import ReportArchive
from app.db.repositories import (
    alert_repository,
    dashboard_repository,
    log_repository,
    report_repository,
)
from app.integrations.cloudwatch import emit_metric
from app.integrations.storage import generate_report_object_key, get_storage
from app.services.export_service import generate_csv_string, get_export_max_rows


def generate_security_summary_markdown(
    start: datetime,
    end: datetime,
    summary_data: Dict[str, Any],
    severities: list,
) -> str:
    """Generates Markdown security audit summary document."""
    from_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# APEye API Security Audit Report",
        "",
        f"- **Generated At**: {now_str}",
        f"- **Audit Period**: {from_str} to {to_str}",
        "",
        "## Executive Summary",
        "",
        f"- **Total API Requests**: {summary_data['total_requests']:,}",
        f"- **Successful Requests (< 400)**: {summary_data['successful_requests']:,}",
        f"- **Failed Requests (>= 400)**: {summary_data['failed_requests']:,}",
        f"- **Total Security Alerts**: {summary_data['total_alerts']:,}",
        f"- **High Severity Alerts**: {summary_data['high_severity_alerts']:,}",
        f"- **Distinct Suspicious IPs**: {summary_data['distinct_suspicious_ips']:,}",
        "",
        "## Threat Severity Breakdown",
        "",
        "| Severity | Alert Count |",
        "|---|---|",
    ]
    for s in severities:
        lines.append(f"| {s['severity']} | {s['count']:,} |")

    lines.append("")
    lines.append("---")
    lines.append("*Generated automatically by APEye API Security Monitoring Platform.*")
    return "\n".join(lines)


def create_archive_artifact(
    session: Session,
    report_type: str,
    start: datetime,
    end: datetime,
    filters: Optional[Dict[str, Any]] = None,
    created_by: Optional[int] = None,
) -> ReportArchive:
    """Produces the archive payload, uploads to storage, and persists the archive record."""
    storage = get_storage()
    now_utc = datetime.now(timezone.utc)
    max_rows = get_export_max_rows()

    if report_type == "LOGS_CSV":
        logs = log_repository.fetch_logs_for_export(
            session=session,
            start=start,
            end=end,
            limit=max_rows,
        )
        headers = [
            "id",
            "request_id",
            "occurred_at",
            "source_ip",
            "path",
            "method",
            "status_code",
            "response_time_ms",
            "auth_outcome",
            "user_id",
        ]
        rows = [
            [
                item.id,
                item.request_id,
                item.occurred_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                item.source_ip,
                item.path,
                item.method,
                item.status_code,
                item.response_time_ms,
                item.auth_outcome,
                item.user_id or "",
            ]
            for item in logs
        ]
        csv_text = generate_csv_string(headers, rows)
        payload = gzip.compress(csv_text.encode("utf-8"))
        content_type = "application/gzip"
        extension = "csv.gz"

    elif report_type == "ALERTS_CSV":
        alerts = alert_repository.fetch_alerts_for_export(
            session=session,
            start=start,
            end=end,
            limit=max_rows,
        )
        headers = [
            "id",
            "category",
            "severity",
            "status",
            "source_ip",
            "request_count",
            "window_seconds",
            "event_count",
            "first_detected_at",
            "last_detected_at",
        ]
        rows = [
            [
                a.id,
                a.category,
                a.severity,
                a.status,
                a.source_ip,
                a.request_count,
                a.window_seconds,
                a.event_count,
                a.first_detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                a.last_detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ]
            for a in alerts
        ]
        csv_text = generate_csv_string(headers, rows)
        payload = csv_text.encode("utf-8")
        content_type = "text/csv"
        extension = "csv"

    elif report_type == "SUMMARY":
        summary_data = dashboard_repository.get_dashboard_summary(session, start, end)
        severities = dashboard_repository.get_dashboard_alert_severity(session, start, end)
        md_text = generate_security_summary_markdown(start, end, summary_data, severities)
        payload = md_text.encode("utf-8")
        content_type = "text/markdown"
        extension = "md"

    else:
        raise ValueError(f"Unsupported report_type: {report_type}")

    object_key = generate_report_object_key(report_type, now_utc, extension)

    metadata = {
        "report_type": report_type,
        "range_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range_end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "creator_id": str(created_by or "system"),
    }

    # Upload to storage backend (Local or S3)
    try:
        info = storage.upload_bytes(
            key=object_key,
            data=payload,
            content_type=content_type,
            metadata=metadata,
        )
    except Exception:
        emit_metric("ReportUploadsFailed")
        raise

    # Persist report archive record in database
    archive_record = report_repository.create_report_archive(
        session=session,
        report_type=report_type,
        object_key=object_key,
        storage_backend=info.backend,
        content_type=info.content_type,
        size_bytes=info.size_bytes,
        sha256=info.sha256,
        range_start=start,
        range_end=end,
        filters=filters or {},
        created_by=created_by,
    )
    session.commit()
    return archive_record
