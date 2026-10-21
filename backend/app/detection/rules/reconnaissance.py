"""Rule C: Reconnaissance / Scanning Detection.

Triggers on 4xx event when within window:
- distinct normalized paths >= 15 AND
- total requests >= 20 AND
- 4xx ratio >= 0.5.
All three conditions must hold.
Sensitive patterns hits (>= 3) bump severity.
"""

from datetime import timedelta
from typing import List, Optional, Set

from app.detection.detection_settings import DetectionSettings
from app.detection.interfaces import WindowCounter
from app.detection.severity import bump, severity_from_ratio
from app.schemas.common import ThreatCategory
from app.schemas.detection import DetectionResult, RequestEvent


class ReconnaissanceRule:
    category = ThreatCategory.RECONNAISSANCE

    def __init__(self, settings: Optional[DetectionSettings] = None) -> None:
        self.settings = settings or DetectionSettings()

    def evaluate(self, event: RequestEvent, counter: WindowCounter) -> Optional[DetectionResult]:
        # Trigger guard: status must be in 4xx range
        if not (400 <= event.status_code <= 499):
            return None

        window_sec = self.settings.recon_window_seconds
        start = event.occurred_at - timedelta(seconds=window_sec)
        end = event.occurred_at

        profile = counter.endpoint_profile(
            source_ip=event.source_ip,
            start=start,
            end=end,
        )

        min_distinct = self.settings.recon_min_distinct
        min_requests = self.settings.recon_min_requests
        min_error_ratio = self.settings.recon_min_error_ratio

        # Condition 1: distinct paths >= min_distinct
        if profile.distinct_paths < min_distinct:
            return None

        # Condition 2: total requests >= min_requests
        if profile.total_requests < min_requests:
            return None

        # Condition 3: 4xx error ratio >= min_error_ratio
        if profile.total_requests <= 0:
            return None
        error_ratio = profile.error_count / profile.total_requests
        if error_ratio < min_error_ratio:
            return None

        # Severity ratio uses distinct paths over the minimum threshold
        severity = severity_from_ratio(profile.distinct_paths, min_distinct)

        # Sensitive-pattern matching across observed paths
        observed_paths: List[str] = [path for path, _ in profile.top_paths]
        if event.path not in observed_paths:
            observed_paths.append(event.path)
        if event.normalized_path not in observed_paths:
            observed_paths.append(event.normalized_path)

        sensitive_hits: Set[str] = set()
        for pattern in self.settings.recon_sensitive_patterns:
            pattern_lower = pattern.lower()
            for path in observed_paths:
                if pattern_lower in path.lower():
                    sensitive_hits.add(pattern)
                    break

        # Bumps severity when 3 or more sensitive patterns are hit
        if len(sensitive_hits) >= 3:
            severity = bump(severity)

        top_endpoints = [path for path, _ in profile.top_paths[:10]]
        if not top_endpoints:
            top_endpoints = [event.path]

        evidence = {
            "distinct_count": profile.distinct_paths,
            "total": profile.total_requests,
            "error_ratio": round(error_ratio, 4),
            "top_paths": top_endpoints[:5],
            "sensitive_pattern_hits": sorted(list(sensitive_hits)),
        }

        return DetectionResult(
            category=self.category,
            severity=severity,
            source_ip=event.source_ip,
            user_id=event.user_id,
            endpoints=top_endpoints[:10],
            request_count=profile.total_requests,
            window_seconds=window_sec,
            threshold=min_requests,
            evidence=evidence,
            dedup_key=f"RECONNAISSANCE:{event.source_ip}",
            detected_at=event.occurred_at,
        )
