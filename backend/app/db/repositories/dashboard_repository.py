"""Dashboard aggregate queries repository (Owner: Anvi).

Executes efficient SQL aggregation queries and produces zero-filled bucket series.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models.alert import Alert
from app.db.models.log import ApiRequestLog


def parse_interval(interval_str: str) -> timedelta:
    """Parses interval string (e.g. '1m', '5m', '15m', '1h', '6h', '1d') into a timedelta."""
    val = interval_str.strip().lower()
    if val.endswith("m"):
        return timedelta(minutes=max(1, int(val[:-1])))
    elif val.endswith("h"):
        return timedelta(hours=max(1, int(val[:-1])))
    elif val.endswith("d"):
        return timedelta(days=max(1, int(val[:-1])))
    elif val.endswith("s"):
        return timedelta(seconds=max(1, int(val[:-1])))
    return timedelta(hours=1)


def get_dashboard_summary(
    session: Session,
    start: datetime,
    end: datetime,
) -> Dict[str, Any]:
    """Computes summary statistics in SQL over the specified time range."""
    # 1. Request logs aggregate
    req_stmt = select(
        func.count(ApiRequestLog.id).label("total"),
        func.sum(
            case(
                (ApiRequestLog.status_code < 400, 1),
                else_=0,
            )
        ).label("successful"),
        func.sum(
            case(
                (ApiRequestLog.status_code >= 400, 1),
                else_=0,
            )
        ).label("failed"),
    ).where(
        ApiRequestLog.occurred_at >= start,
        ApiRequestLog.occurred_at < end,
    )
    req_row = session.execute(req_stmt).one()
    total_req = req_row.total or 0
    successful_req = int(req_row.successful or 0)
    failed_req = int(req_row.failed or 0)

    # 2. Alerts aggregate
    alert_stmt = select(
        func.count(Alert.id).label("total_alerts"),
        func.sum(
            case(
                (Alert.severity == "HIGH", 1),
                else_=0,
            )
        ).label("high_alerts"),
        func.count(func.distinct(Alert.source_ip)).label("distinct_ips"),
    ).where(
        Alert.first_detected_at >= start,
        Alert.first_detected_at < end,
    )
    alert_row = session.execute(alert_stmt).one()
    total_alerts = alert_row.total_alerts or 0
    high_alerts = int(alert_row.high_alerts or 0)
    distinct_ips = alert_row.distinct_ips or 0

    return {
        "window": {
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "total_requests": total_req,
        "successful_requests": successful_req,
        "failed_requests": failed_req,
        "total_alerts": total_alerts,
        "high_severity_alerts": high_alerts,
        "distinct_suspicious_ips": distinct_ips,
    }


def get_dashboard_traffic(
    session: Session,
    start: datetime,
    end: datetime,
    interval_str: str = "1h",
) -> Dict[str, Any]:
    """Generates zero-filled traffic bucket time series."""
    step = parse_interval(interval_str)

    # Pre-generate all zero-filled bucket timestamps
    bucket_map: Dict[datetime, Dict[str, int]] = {}
    curr = start
    while curr < end:
        bucket_map[curr] = {"total": 0, "successful": 0, "failed": 0}
        curr += step

    # Fetch logs in window
    stmt = select(ApiRequestLog.occurred_at, ApiRequestLog.status_code).where(
        ApiRequestLog.occurred_at >= start,
        ApiRequestLog.occurred_at < end,
    )
    rows = session.execute(stmt).all()

    # Place logs into appropriate buckets
    step_seconds = step.total_seconds()
    for row_time, status_code in rows:
        offset_sec = (row_time - start).total_seconds()
        bucket_idx = int(offset_sec // step_seconds)
        bucket_time = start + timedelta(seconds=bucket_idx * step_seconds)
        if bucket_time in bucket_map:
            b = bucket_map[bucket_time]
            b["total"] += 1
            if status_code < 400:
                b["successful"] += 1
            else:
                b["failed"] += 1

    points = [
        {
            "bucket_start": b_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total": counts["total"],
            "successful": counts["successful"],
            "failed": counts["failed"],
        }
        for b_time, counts in sorted(bucket_map.items())
    ]

    return {"interval": interval_str, "points": points}


def get_dashboard_status_distribution(
    session: Session,
    start: datetime,
    end: datetime,
) -> Dict[str, Any]:
    """Aggregates HTTP response status classes (2xx..5xx) and specific status codes."""
    stmt = (
        select(
            ApiRequestLog.status_code,
            func.count(ApiRequestLog.id).label("cnt"),
        )
        .where(
            ApiRequestLog.occurred_at >= start,
            ApiRequestLog.occurred_at < end,
        )
        .group_by(ApiRequestLog.status_code)
        .order_by(ApiRequestLog.status_code.asc())
    )
    rows = session.execute(stmt).all()

    classes_map: Dict[str, int] = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
    codes_list: List[Dict[str, int]] = []

    for code, cnt in rows:
        codes_list.append({"status_code": code, "count": cnt})
        class_key = f"{code // 100}xx"
        classes_map[class_key] = classes_map.get(class_key, 0) + cnt

    classes_list = [
        {"status_class": k, "count": v}
        for k, v in sorted(classes_map.items())
        if v > 0 or k in ("2xx", "4xx", "5xx")
    ]

    return {"classes": classes_list, "codes": codes_list}


def get_dashboard_top_endpoints(
    session: Session,
    start: datetime,
    end: datetime,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Returns top endpoints by request volume with corresponding error counts."""
    stmt = (
        select(
            ApiRequestLog.normalized_path.label("endpoint"),
            func.count(ApiRequestLog.id).label("request_count"),
            func.sum(
                case(
                    (ApiRequestLog.status_code >= 400, 1),
                    else_=0,
                )
            ).label("error_count"),
        )
        .where(
            ApiRequestLog.occurred_at >= start,
            ApiRequestLog.occurred_at < end,
        )
        .group_by(ApiRequestLog.normalized_path)
        .order_by(func.count(ApiRequestLog.id).desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    return [
        {
            "endpoint": r.endpoint,
            "request_count": r.request_count,
            "error_count": int(r.error_count or 0),
        }
        for r in rows
    ]


def get_dashboard_response_times(
    session: Session,
    start: datetime,
    end: datetime,
    interval_str: str = "1h",
) -> Dict[str, Any]:
    """Computes avg, p95, and max response times per time bucket, zero-filled."""
    step = parse_interval(interval_str)

    # Initialize buckets with lists of response times
    bucket_map: Dict[datetime, List[int]] = {}
    curr = start
    while curr < end:
        bucket_map[curr] = []
        curr += step

    stmt = select(ApiRequestLog.occurred_at, ApiRequestLog.response_time_ms).where(
        ApiRequestLog.occurred_at >= start,
        ApiRequestLog.occurred_at < end,
    )
    rows = session.execute(stmt).all()

    step_seconds = step.total_seconds()
    for row_time, ms in rows:
        offset_sec = (row_time - start).total_seconds()
        bucket_idx = int(offset_sec // step_seconds)
        bucket_time = start + timedelta(seconds=bucket_idx * step_seconds)
        if bucket_time in bucket_map:
            bucket_map[bucket_time].append(ms)

    points = []
    for b_time, values in sorted(bucket_map.items()):
        if values:
            values.sort()
            avg_val = round(sum(values) / len(values), 1)
            # 95th percentile
            p95_idx = int(len(values) * 0.95)
            p95_idx = min(p95_idx, len(values) - 1)
            p95_val = float(values[p95_idx])
            max_val = values[-1]
        else:
            avg_val = 0.0
            p95_val = 0.0
            max_val = 0

        points.append(
            {
                "bucket_start": b_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "avg_ms": avg_val,
                "p95_ms": p95_val,
                "max_ms": max_val,
            }
        )

    return {"interval": interval_str, "points": points}


def get_dashboard_alert_severity(
    session: Session,
    start: datetime,
    end: datetime,
) -> List[Dict[str, Any]]:
    """Returns alert counts grouped by severity, guaranteed to always include LOW, MEDIUM, and HIGH."""
    stmt = (
        select(
            Alert.severity,
            func.count(Alert.id).label("cnt"),
        )
        .where(
            Alert.first_detected_at >= start,
            Alert.first_detected_at < end,
        )
        .group_by(Alert.severity)
    )
    rows = session.execute(stmt).all()
    counts = {r.severity: r.cnt for r in rows}

    return [
        {"severity": "LOW", "count": counts.get("LOW", 0)},
        {"severity": "MEDIUM", "count": counts.get("MEDIUM", 0)},
        {"severity": "HIGH", "count": counts.get("HIGH", 0)},
    ]
