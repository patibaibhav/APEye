"""CloudWatch operational logging and buffered metrics integration (Owner: Anvi).

Follows cloudwatch-contract.md:
- configure_cloudwatch_logging(settings): Attaches watchtower handler when CLOUDWATCH_ENABLED=true
- emit_metric(name, value=1.0, unit="Count"): Thread-safe buffered metric recording
- flush_metrics(): Pushes buffered metrics to CloudWatch in batches
- Resilient: CloudWatch outages never crash the application or fail client requests
"""

import logging
import os
import socket
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_METRICS_BUFFER: List[Dict[str, Any]] = []
_METRICS_LOCK = threading.Lock()
_MAX_BUFFER_SIZE = 1000


def is_cloudwatch_enabled() -> bool:
    """Checks if CloudWatch integration is enabled in configuration."""
    return os.getenv("CLOUDWATCH_ENABLED", "false").lower() in ("true", "1", "yes")


def configure_cloudwatch_logging(log_level: str = "INFO") -> None:
    """Attaches Watchtower logging handler to the operational logger if enabled."""
    if not is_cloudwatch_enabled():
        return

    try:
        import boto3
        import watchtower

        log_group = os.getenv("CW_LOG_GROUP", "/api-security-monitor/app")
        stream_prefix = os.getenv("CW_LOG_STREAM_PREFIX", "local-dev")
        region = os.getenv("AWS_REGION", "us-east-1")
        hostname = socket.gethostname()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stream_name = f"{stream_prefix}-{hostname}-{today}"

        boto_client = boto3.client("logs", region_name=region)
        cw_handler = watchtower.CloudWatchLogHandler(
            log_group_name=log_group,
            log_stream_name=stream_name,
            boto3_client=boto_client,
            send_interval=10,
        )
        cw_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        ops_logger = logging.getLogger("app.ops")
        ops_logger.addHandler(cw_handler)
    except Exception as exc:
        print(f"[WARN] Failed to configure CloudWatch logging: {exc}", file=sys.stderr)


def emit_metric(
    name: str,
    value: float = 1.0,
    unit: str = "Count",
    dimensions: Optional[Dict[str, str]] = None,
) -> None:
    """Buffers a custom metric measurement for periodic or shutdown flushing."""
    if not is_cloudwatch_enabled():
        return

    now = datetime.now(timezone.utc)
    metric_datum: Dict[str, Any] = {
        "MetricName": name,
        "Value": float(value),
        "Unit": unit,
        "Timestamp": now,
    }
    if dimensions:
        metric_datum["Dimensions"] = [{"Name": k, "Value": v} for k, v in dimensions.items()]

    with _METRICS_LOCK:
        if len(_METRICS_BUFFER) < _MAX_BUFFER_SIZE:
            _METRICS_BUFFER.append(metric_datum)
        else:
            # Drop excess bounded metrics under heavy backpressure
            print(
                f"[WARN] CloudWatch metrics buffer full, dropping metric: {name}", file=sys.stderr
            )


def flush_metrics() -> None:
    """Pushes buffered metrics to AWS CloudWatch using PutMetricData."""
    if not is_cloudwatch_enabled():
        return

    with _METRICS_LOCK:
        if not _METRICS_BUFFER:
            return
        to_flush = list(_METRICS_BUFFER)
        _METRICS_BUFFER.clear()

    try:
        import boto3

        namespace = os.getenv("CW_METRICS_NAMESPACE", "ApiSecurityMonitor")
        region = os.getenv("AWS_REGION", "us-east-1")
        client = boto3.client("cloudwatch", region_name=region)

        # CloudWatch PutMetricData accepts up to 1000 MetricData items in a single call
        # Batch in chunks of 20 to stay well under API limits
        chunk_size = 20
        for i in range(0, len(to_flush), chunk_size):
            chunk = to_flush[i : i + chunk_size]
            client.put_metric_data(
                Namespace=namespace,
                MetricData=chunk,
            )
    except Exception as exc:
        # CloudWatch outage must never fail the application: log to stderr and gracefully continue
        print(f"[WARN] CloudWatch flush_metrics failed: {exc}", file=sys.stderr)
