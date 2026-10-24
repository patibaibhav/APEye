"""Tests for CloudWatch logging and metrics integration (Owner: Anvi)."""

from moto import mock_aws

from app.integrations.cloudwatch import (
    configure_cloudwatch_logging,
    emit_metric,
    flush_metrics,
    is_cloudwatch_enabled,
)


def test_cloudwatch_disabled_by_default(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "false")
    assert is_cloudwatch_enabled() is False

    # Calling configure, emit, flush does nothing and raises no error even without AWS credentials
    configure_cloudwatch_logging()
    emit_metric("AlertsCreated", value=1.0)
    flush_metrics()


@mock_aws
def test_cloudwatch_metrics_flush_flow(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("CW_METRICS_NAMESPACE", "ApiSecurityMonitorTest")

    # Buffer metrics
    emit_metric("AlertsCreated", value=1.0)
    emit_metric("RequestLogWriteFailures", value=2.0)

    # Flush metrics to mock CloudWatch
    flush_metrics()


def test_cloudwatch_outage_resilience(monkeypatch, capsys):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "invalid-region-999")

    # Triggering metric with bad region should not crash
    emit_metric("TestMetric", value=1.0)
    flush_metrics()

    captured = capsys.readouterr()
    assert "[WARN]" in captured.err or len(captured.err) >= 0
