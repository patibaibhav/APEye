"""Rule B: Request Rate (Excessive Requests) Detection.

Triggers on any event when request count from a single IP within window exceeds threshold.
"""

from datetime import timedelta
from typing import Optional

from app.detection.detection_settings import DetectionSettings
from app.detection.interfaces import WindowCounter
from app.detection.severity import severity_from_ratio
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, RequestEvent


class RequestRateRule:
    category = ThreatCategory.EXCESSIVE_REQUESTS

    def __init__(self, settings: Optional[DetectionSettings] = None) -> None:
        self.settings = settings or DetectionSettings()

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        window_sec = self.settings.rate_window_seconds
        start = event.occurred_at - timedelta(seconds=window_sec)
        end = event.occurred_at

        count = counter.count_requests(
            source_ip=event.source_ip,
            start=start,
            end=end,
        )

        threshold = self.settings.rate_threshold
        # Condition: strictly greater than threshold
        if count <= threshold:
            return None

        severity = severity_from_ratio(count, threshold)

        # Retrieve endpoint profile to populate top paths
        try:
            profile = counter.endpoint_profile(
                source_ip=event.source_ip,
                start=start,
                end=end,
            )
            top_paths = [path for path, _ in profile.top_paths[:5]]
        except Exception:
            top_paths = [event.path]

        if not top_paths:
            top_paths = [event.path]

        evidence = {
            "count": count,
            "window_seconds": window_sec,
            "top_paths": top_paths,
        }

        return DetectionResult(
            category=self.category,
            severity=severity,
            source_ip=event.source_ip,
            user_id=event.user_id,
            endpoints=top_paths[:10],
            request_count=count,
            window_seconds=window_sec,
            threshold=threshold,
            evidence=evidence,
            dedup_key=f"EXCESSIVE_REQUESTS:{event.source_ip}",
            detected_at=event.occurred_at,
        )
