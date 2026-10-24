"""SQLAlchemy models registry (Owner: Anvi).

Registers all six database contract tables on Base.metadata:
1. users
2. api_request_logs
3. alerts
4. alert_notes
5. ip_investigations
6. report_archives
"""

from app.db.base import Base
from app.db.models.alert import Alert, AlertNote
from app.db.models.investigation import IpInvestigation
from app.db.models.log import ApiRequestLog
from app.db.models.report import ReportArchive
from app.db.models.user import User

__all__ = [
    "Base",
    "User",
    "ApiRequestLog",
    "Alert",
    "AlertNote",
    "IpInvestigation",
    "ReportArchive",
]
