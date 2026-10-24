"""Window counter repository implementing WindowCounter protocol with parameterized SQL queries (Owner: Anvi)."""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models.log import ApiRequestLog
from app.detection.interfaces import WindowCounter
from app.schemas.detection import EndpointProfile


class SqlWindowCounter(WindowCounter):
    """SQL-backed WindowCounter querying api_request_logs over half-open time windows (start, end]."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def count_requests(self, *, source_ip: str, start: datetime, end: datetime) -> int:
        """Counts total requests from source_ip in (start, end]."""
        stmt = select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.source_ip == source_ip,
            ApiRequestLog.occurred_at > start,
            ApiRequestLog.occurred_at <= end,
        )
        return self.session.execute(stmt).scalar() or 0

    def count_by_status(
        self,
        *,
        statuses: Sequence[int],
        start: datetime,
        end: datetime,
        source_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        exclude_path: Optional[str] = None,
    ) -> int:
        """Counts requests matching status codes in (start, end], optionally filtered by IP, user_id, or excluded path."""
        stmt = select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.status_code.in_(statuses),
            ApiRequestLog.occurred_at > start,
            ApiRequestLog.occurred_at <= end,
        )
        if source_ip is not None:
            stmt = stmt.where(ApiRequestLog.source_ip == source_ip)
        if user_id is not None:
            stmt = stmt.where(ApiRequestLog.user_id == user_id)
        if exclude_path is not None:
            stmt = stmt.where(ApiRequestLog.path != exclude_path)

        return self.session.execute(stmt).scalar() or 0

    def count_login_failures(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> int:
        """Counts 401 POST login failures from source_ip in (start, end]."""
        stmt = select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.source_ip == source_ip,
            ApiRequestLog.method == "POST",
            ApiRequestLog.path == login_path,
            ApiRequestLog.status_code == 401,
            ApiRequestLog.occurred_at > start,
            ApiRequestLog.occurred_at <= end,
        )
        return self.session.execute(stmt).scalar() or 0

    def has_login_success(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> bool:
        """Checks if any successful login occurred from source_ip in (start, end]."""
        stmt = select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.source_ip == source_ip,
            ApiRequestLog.method == "POST",
            ApiRequestLog.path == login_path,
            ApiRequestLog.status_code == 200,
            ApiRequestLog.occurred_at > start,
            ApiRequestLog.occurred_at <= end,
        )
        count = self.session.execute(stmt).scalar() or 0
        return count > 0

    def endpoint_profile(
        self,
        *,
        source_ip: str,
        start: datetime,
        end: datetime,
    ) -> EndpointProfile:
        """Returns aggregate endpoint profile for reconnaissance detection."""
        # Aggregate totals in SQL
        agg_stmt = select(
            func.count(ApiRequestLog.id).label("total_requests"),
            func.count(func.distinct(ApiRequestLog.path)).label("distinct_paths"),
            func.sum(
                case(
                    (ApiRequestLog.status_code.between(400, 499), 1),
                    else_=0,
                )
            ).label("error_count"),
        ).where(
            ApiRequestLog.source_ip == source_ip,
            ApiRequestLog.occurred_at > start,
            ApiRequestLog.occurred_at <= end,
        )
        row = self.session.execute(agg_stmt).one()
        total_requests = row.total_requests or 0
        distinct_paths = row.distinct_paths or 0
        error_count = int(row.error_count or 0)

        # Top paths
        top_stmt = (
            select(ApiRequestLog.path, func.count(ApiRequestLog.id).label("cnt"))
            .where(
                ApiRequestLog.source_ip == source_ip,
                ApiRequestLog.occurred_at > start,
                ApiRequestLog.occurred_at <= end,
            )
            .group_by(ApiRequestLog.path)
            .order_by(func.count(ApiRequestLog.id).desc())
            .limit(10)
        )
        top_rows = self.session.execute(top_stmt).all()
        top_paths = [(r[0], r[1]) for r in top_rows]

        return EndpointProfile(
            total_requests=total_requests,
            distinct_paths=distinct_paths,
            error_count=error_count,
            top_paths=top_paths,
        )
