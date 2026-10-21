"""Test fixtures and in-memory FakeWindowCounter for detection rule testing."""

from collections import Counter
from datetime import datetime
from typing import List, Optional, Sequence
import pytest

from app.detection.interfaces import WindowCounter
from app.schemas.detection import EndpointProfile, RequestEvent


class FakeWindowCounter(WindowCounter):
    """In-memory event store implementing WindowCounter with half-open window (start, end] semantics."""

    def __init__(self, events: Optional[List[RequestEvent]] = None) -> None:
        self.events: List[RequestEvent] = list(events) if events else []
        self.should_raise: bool = False

    def add_event(self, event: RequestEvent) -> None:
        self.events.append(event)

    def count_requests(self, *, source_ip: str, start: datetime, end: datetime) -> int:
        if self.should_raise:
            raise RuntimeError("Simulated counter database failure")
        return sum(
            1
            for e in self.events
            if e.source_ip == source_ip and start < e.occurred_at <= end
        )

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
        if self.should_raise:
            raise RuntimeError("Simulated counter database failure")
        count = 0
        status_set = set(statuses)
        for e in self.events:
            if not (start < e.occurred_at <= end):
                continue
            if e.status_code not in status_set:
                continue
            if source_ip is not None and e.source_ip != source_ip:
                continue
            if user_id is not None and e.user_id != user_id:
                continue
            if exclude_path is not None and e.path == exclude_path:
                continue
            count += 1
        return count

    def count_login_failures(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> int:
        if self.should_raise:
            raise RuntimeError("Simulated counter database failure")
        return sum(
            1
            for e in self.events
            if e.source_ip == source_ip
            and e.path == login_path
            and e.status_code == 401
            and start < e.occurred_at <= end
        )

    def has_login_success(
        self,
        *,
        source_ip: str,
        login_path: str,
        start: datetime,
        end: datetime,
    ) -> bool:
        if self.should_raise:
            raise RuntimeError("Simulated counter database failure")
        return any(
            e.source_ip == source_ip
            and e.path == login_path
            and e.status_code == 200
            and start < e.occurred_at <= end
            for e in self.events
        )

    def endpoint_profile(
        self,
        *,
        source_ip: str,
        start: datetime,
        end: datetime,
    ) -> EndpointProfile:
        if self.should_raise:
            raise RuntimeError("Simulated counter database failure")
        ip_events = [
            e for e in self.events if e.source_ip == source_ip and start < e.occurred_at <= end
        ]
        total = len(ip_events)
        distinct = len({e.normalized_path for e in ip_events})
        errors = sum(1 for e in ip_events if 400 <= e.status_code <= 499)
        path_counts = Counter(e.path for e in ip_events)
        top_paths = path_counts.most_common(10)
        return EndpointProfile(
            total_requests=total,
            distinct_paths=distinct,
            error_count=errors,
            top_paths=top_paths,
        )


@pytest.fixture
def fake_counter() -> FakeWindowCounter:
    return FakeWindowCounter()
