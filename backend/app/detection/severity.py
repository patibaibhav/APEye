"""Severity calculation and progression logic.

Frozen rules:
- severity_from_ratio(count, threshold):
  - ratio < 1.5 -> LOW
  - 1.5 <= ratio < 3.0 -> MEDIUM
  - ratio >= 3.0 -> HIGH
- bump(severity):
  - raises one level, capped at HIGH
"""

from app.schemas.common import Severity


def severity_from_ratio(count: int, threshold: int) -> Severity:
    """Calculates Severity from observed event count and configured threshold."""
    if threshold <= 0:
        ratio = float(count)
    else:
        ratio = count / threshold

    if ratio < 1.5:
        return Severity.LOW
    elif ratio < 3.0:
        return Severity.MEDIUM
    else:
        return Severity.HIGH


def bump(severity: Severity) -> Severity:
    """Raises severity by one level, capped at HIGH."""
    if severity == Severity.LOW:
        return Severity.MEDIUM
    return Severity.HIGH
