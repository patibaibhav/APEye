"""Unit tests for severity calculation and bump progression."""

from app.detection.severity import bump, severity_from_ratio
from app.schemas.common import Severity


def test_severity_from_ratio_boundaries():
    # Exactly at ratio 1.0 (threshold) -> LOW
    assert severity_from_ratio(10, 10) == Severity.LOW
    
    # Just below 1.5 -> LOW
    assert severity_from_ratio(14, 10) == Severity.LOW

    # Exactly at boundary 1.5 -> MEDIUM
    assert severity_from_ratio(15, 10) == Severity.MEDIUM

    # In medium range (e.g. 2.0, 2.9) -> MEDIUM
    assert severity_from_ratio(20, 10) == Severity.MEDIUM
    assert severity_from_ratio(29, 10) == Severity.MEDIUM

    # Exactly at boundary 3.0 -> HIGH
    assert severity_from_ratio(30, 10) == Severity.HIGH

    # Above 3.0 -> HIGH
    assert severity_from_ratio(50, 10) == Severity.HIGH


def test_severity_zero_or_negative_threshold():
    # Defensive behavior when threshold is 0
    assert severity_from_ratio(1, 0) == Severity.LOW
    assert severity_from_ratio(2, 0) == Severity.MEDIUM
    assert severity_from_ratio(3, 0) == Severity.HIGH


def test_bump_progression():
    assert bump(Severity.LOW) == Severity.MEDIUM
    assert bump(Severity.MEDIUM) == Severity.HIGH
    assert bump(Severity.HIGH) == Severity.HIGH
