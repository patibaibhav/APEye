"""Detection Engine: orchestrates evaluation of detection rules in fixed order.

Engine order: Brute Force (A) -> Request Rate (B) -> Unauthorized Access (D) -> Reconnaissance (C).
Each rule execution is isolated with try/except so one rule failure never stops others.
"""

from typing import List, Optional, Sequence

from app.core.logging_config import get_ops_logger
from app.detection.detection_settings import DetectionSettings
from app.detection.interfaces import Rule, WindowCounter
from app.detection.rules.brute_force import BruteForceRule
from app.detection.rules.reconnaissance import ReconnaissanceRule
from app.detection.rules.request_rate import RequestRateRule
from app.detection.rules.unauthorized_access import UnauthorizedAccessRule
from app.schemas.detection import DetectionResult, RequestEvent


class DetectionEngine:
    """Evaluates request events against registered rules sequentially."""

    def __init__(self, rules: Sequence[Rule]) -> None:
        self.rules: List[Rule] = list(rules)
        self.error_count: int = 0

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> List[DetectionResult]:
        """Evaluates an event against all configured rules.

        Exceptions in any rule are logged and isolated without halting other rules.
        """
        results: List[DetectionResult] = []
        ops_logger = get_ops_logger()

        for rule in self.rules:
            rule_name = type(rule).__name__
            try:
                result = rule.evaluate(event, counter)
                if result is not None:
                    results.append(result)
            except Exception as exc:
                self.error_count += 1
                ops_logger.error(
                    "detection_rule_error",
                    extra={
                        "extra_fields": {
                            "rule": rule_name,
                            "request_id": event.request_id,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    },
                )

        return results


def build_default_engine(settings: Optional[DetectionSettings] = None) -> DetectionEngine:
    """Builds the default detection engine configured with rules A, B, D, C."""
    cfg = settings or DetectionSettings()
    rules = [
        BruteForceRule(settings=cfg),
        RequestRateRule(settings=cfg),
        UnauthorizedAccessRule(settings=cfg),
        ReconnaissanceRule(settings=cfg),
    ]
    return DetectionEngine(rules=rules)
