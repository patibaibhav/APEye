"""Rule A: Brute Force Detection.

Triggers on POST to login path resulting in 401.
Alerts when failed logins from the same IP within window exceed threshold.
Bumps severity if followed by a successful login.
"""

from datetime import timedelta
from typing import Optional

from app.detection.detection_settings import DetectionSettings
from app.detection.interfaces import WindowCounter
from app.detection.severity import bump, severity_from_ratio
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, RequestEvent


class BruteForceRule:
    category = ThreatCategory.BRUTE_FORCE

    def __init__(self, settings: Optional[DetectionSettings] = None) -> None:
        self.settings = settings or DetectionSettings()

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        # Trigger guard: Must be POST to LOGIN_PATH with 401
        if not (
            event.method == "POST"
            and event.path == self.settings.login_path
            and event.status_code == 401
        ):
            return None

        window_sec = self.settings.brute_force_window_seconds
        start = event.occurred_at - timedelta(seconds=window_sec)
        end = event.occurred_at

        failures = counter.count_login_failures(
            source_ip=event.source_ip,
            login_path=self.settings.login_path,
            start=start,
            end=end,
        )

        threshold = self.settings.brute_force_threshold
        # Condition: strictly greater than threshold
        if failures <= threshold:
            return None

        severity = severity_from_ratio(failures, threshold)
        has_success = counter.has_login_success(
            source_ip=event.source_ip,
            login_path=self.settings.login_path,
            start=start,
            end=end,
        )
        if has_success:
            severity = bump(severity)

        evidence = {
            "count": failures,
            "window_seconds": window_sec,
            "first_failure_at": start.isoformat(),
            "last_failure_at": end.isoformat(),
            "login_success_after_failures": has_success,
        }

        return DetectionResult(
            category=self.category,
            severity=severity,
            source_ip=event.source_ip,
            user_id=event.user_id,
            endpoints=[event.path],
            request_count=failures,
            window_seconds=window_sec,
            threshold=threshold,
            evidence=evidence,
            dedup_key=f"BRUTE_FORCE:{event.source_ip}",
            detected_at=event.occurred_at,
        )
