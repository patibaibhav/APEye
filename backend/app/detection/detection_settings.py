"""Detection configuration settings (Owner: Baibhav).

All values are environment-configurable with frozen defaults.
"""

import os
from typing import List
from pydantic import BaseModel, Field


def _parse_comma_list(val: str | None) -> List[str]:
    if not val:
        return []
    return [item.strip() for item in val.split(",") if item.strip()]


class DetectionSettings(BaseModel):
    login_path: str = Field(
        default_factory=lambda: os.getenv("DET_LOGIN_PATH", "/api/auth/login")
    )
    brute_force_threshold: int = Field(
        default_factory=lambda: int(os.getenv("DET_BRUTE_FORCE_THRESHOLD", "10"))
    )
    brute_force_window_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DET_BRUTE_FORCE_WINDOW_SECONDS", "300"))
    )
    rate_threshold: int = Field(
        default_factory=lambda: int(os.getenv("DET_RATE_THRESHOLD", "100"))
    )
    rate_window_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DET_RATE_WINDOW_SECONDS", "60"))
    )
    unauth_threshold: int = Field(
        default_factory=lambda: int(os.getenv("DET_UNAUTH_THRESHOLD", "15"))
    )
    unauth_window_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DET_UNAUTH_WINDOW_SECONDS", "600"))
    )
    recon_min_distinct: int = Field(
        default_factory=lambda: int(os.getenv("DET_RECON_MIN_DISTINCT", "15"))
    )
    recon_min_requests: int = Field(
        default_factory=lambda: int(os.getenv("DET_RECON_MIN_REQUESTS", "20"))
    )
    recon_min_error_ratio: float = Field(
        default_factory=lambda: float(os.getenv("DET_RECON_MIN_ERROR_RATIO", "0.5"))
    )
    recon_window_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DET_RECON_WINDOW_SECONDS", "120"))
    )
    recon_sensitive_patterns: List[str] = Field(
        default_factory=lambda: _parse_comma_list(
            os.getenv(
                "DET_RECON_SENSITIVE_PATTERNS",
                "/admin,/.env,/.git,/config,/backup,/wp-login,/phpmyadmin,/actuator,/debug",
            )
        )
    )
    alert_cooldown_seconds: int = Field(
        default_factory=lambda: int(os.getenv("DET_ALERT_COOLDOWN_SECONDS", "600"))
    )
    ignore_ips: List[str] = Field(
        default_factory=lambda: _parse_comma_list(os.getenv("DETECTION_IGNORE_IPS", ""))
    )
