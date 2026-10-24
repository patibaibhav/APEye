"""Database repositories registry (Owner: Anvi)."""

from app.db.repositories import (
    alert_repository,
    dashboard_repository,
    ip_investigation_repository,
    log_repository,
    report_repository,
    user_repository,
    window_repository,
)

__all__ = [
    "user_repository",
    "log_repository",
    "alert_repository",
    "ip_investigation_repository",
    "window_repository",
    "dashboard_repository",
    "report_repository",
]
