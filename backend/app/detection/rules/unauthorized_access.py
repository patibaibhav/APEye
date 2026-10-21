"""Rule D: Repeated 401 and 403 (Unauthorized Access) Detection.

Triggers on non-login 401/403 status codes.
Alerts when repeated 401/403 counts exceed threshold within window.
Differentiates dedup key when user_id is present.
"""

from datetime import timedelta
from typing import Optional

from app.detection.detection_settings import DetectionSettings
from app.detection.interfaces import WindowCounter
from app.detection.severity import severity_from_ratio
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, RequestEvent


class UnauthorizedAccessRule:
    category = ThreatCategory.UNAUTHORIZED_ACCESS

    def __init__(self, settings: Optional[DetectionSettings] = None) -> None:
        self.settings = settings or DetectionSettings()

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        # Trigger guard: status must be 401 or 403, and path must NOT be the login path
        if event.status_code not in (401, 403):
            return None
        if event.path == self.settings.login_path:
            return None

        window_sec = self.settings.unauth_window_seconds
        start = event.occurred_at - timedelta(seconds=window_sec)
        end = event.occurred_at

        count = counter.count_by_status(
            statuses=[401, 403],
            start=start,
            end=end,
            source_ip=event.source_ip,
            user_id=event.user_id,
            exclude_path=self.settings.login_path,
        )

        threshold = self.settings.unauth_threshold
        # Condition: strictly greater than threshold
        if count <= threshold:
            return None

        severity = severity_from_ratio(count, threshold)

        # Calculate per-status breakdown safely
        try:
            count_401 = counter.count_by_status(
                statuses=[401],
                start=start,
                end=end,
                source_ip=event.source_ip,
                user_id=event.user_id,
                exclude_path=self.settings.login_path,
            )
            count_403 = counter.count_by_status(
                statuses=[403],
                start=start,
                end=end,
                source_ip=event.source_ip,
                user_id=event.user_id,
                exclude_path=self.settings.login_path,
            )
        except Exception:
            count_401 = count if event.status_code == 401 else 0
            count_403 = count if event.status_code == 403 else 0

        evidence = {
            "count": count,
            "window_seconds": window_sec,
            "per_status": {"401": count_401, "403": count_403},
            "paths": [event.path],
        }

        # Dedup key formatting: separate user variant when user_id is present
        if event.user_id is not None:
            dedup_key = f"UNAUTHORIZED_ACCESS:user:{event.user_id}"
        else:
            dedup_key = f"UNAUTHORIZED_ACCESS:{event.source_ip}"

        return DetectionResult(
            category=self.category,
            severity=severity,
            source_ip=event.source_ip,
            user_id=event.user_id,
            endpoints=[event.path],
            request_count=count,
            window_seconds=window_sec,
            threshold=threshold,
            evidence=evidence,
            dedup_key=dedup_key,
            detected_at=event.occurred_at,
        )
