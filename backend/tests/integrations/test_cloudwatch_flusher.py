"""Tests for the periodic CloudWatch metrics flusher (added for AWS deployment)."""

from moto import mock_aws

from app.integrations import cloudwatch
from app.integrations.cloudwatch import start_metrics_flusher, stop_metrics_flusher


def test_flusher_is_noop_when_cloudwatch_disabled(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "false")
    start_metrics_flusher()
    assert cloudwatch._FLUSH_THREAD is None or not cloudwatch._FLUSH_THREAD.is_alive()
    stop_metrics_flusher()


@mock_aws
def test_flusher_starts_and_stops_when_enabled(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    start_metrics_flusher()
    assert cloudwatch._FLUSH_THREAD is not None and cloudwatch._FLUSH_THREAD.is_alive()
    cloudwatch.emit_metric("AlertsCreated")
    stop_metrics_flusher()
    cloudwatch._FLUSH_THREAD.join(timeout=5)
    assert not cloudwatch._FLUSH_THREAD.is_alive()
