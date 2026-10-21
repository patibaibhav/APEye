"""Request logging ASGI middleware.

Captures normalized RequestEvent per API call without ever affecting client response.
Times requests accurately including streaming body chunks.
Runs event ingestion asynchronously in a threadpool with error isolation.
"""

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Callable, FrozenSet, Optional
import uuid
from starlette.concurrency import run_in_threadpool

from app.core.logging_config import get_ops_logger
from app.middleware.client_ip import resolve_client_ip
from app.middleware.path_normalizer import normalize_path
from app.schemas.common import AuthOutcome
from app.schemas.detection import RequestEvent


class RequestLoggingMiddleware:
    """Pure ASGI middleware for capturing request metadata and triggering background ingestion."""

    def __init__(
        self,
        app: Callable,
        ingest: Callable[[RequestEvent], None],
        trusted_proxy_count: int = 0,
        ignored_paths: Optional[FrozenSet[str]] = None,
    ) -> None:
        self.app = app
        self.ingest = ingest
        self.trusted_proxy_count = trusted_proxy_count
        self.ignored_paths: FrozenSet[str] = (
            ignored_paths if ignored_paths is not None else frozenset({"/api/health"})
        )

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        raw_path = scope.get("path", "")
        # Remove any query string if present in path
        path_only = raw_path.split("?")[0]

        # Only paths starting with /api are recorded, except ignored_paths (/api/health)
        is_recorded = path_only.startswith("/api") and (path_only not in self.ignored_paths)

        # Generate unique request_id
        request_id = str(uuid.uuid4())
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        occurred_at = datetime.now(timezone.utc)
        start_time = perf_counter()

        status_code = 500
        duration_ms = 0
        response_completed = False

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code, duration_ms, response_completed
            msg_type = message.get("type")

            if msg_type == "http.response.start":
                status_code = message.get("status", 200)
                # Attach X-Request-ID header to response start message
                headers = list(message.get("headers", []))
                has_req_id = any(k.lower() == b"x-request-id" for k, _ in headers)
                if not has_req_id:
                    headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers

            elif msg_type == "http.response.body":
                more_body = message.get("more_body", False)
                if not more_body:
                    # Final body chunk sent: measure exact duration
                    response_completed = True
                    duration_ms = max(0, int((perf_counter() - start_time) * 1000))

            res = send(message)
            if asyncio.iscoroutine(res):
                await res

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status_code = 500
            if not response_completed:
                duration_ms = max(0, int((perf_counter() - start_time) * 1000))
            raise
        finally:
            if is_recorded:
                if not response_completed:
                    duration_ms = max(0, int((perf_counter() - start_time) * 1000))

                # Extract peer client IP
                client = scope.get("client")
                peer = client[0] if client else None

                # Extract X-Forwarded-For if present
                headers = scope.get("headers", [])
                xff = None
                for k, v in headers:
                    if k.lower() == b"x-forwarded-for":
                        try:
                            xff = v.decode("latin1")
                        except Exception:
                            xff = None
                        break

                source_ip = resolve_client_ip(peer, xff, self.trusted_proxy_count)
                norm_path = normalize_path(path_only)
                method = scope.get("method", "GET").upper()

                # Extract auth outcome and user_id populated by auth dependency
                state = scope.get("state", {})
                auth_outcome = state.get("auth_outcome", AuthOutcome.NONE)
                if isinstance(auth_outcome, str):
                    try:
                        auth_outcome = AuthOutcome(auth_outcome)
                    except ValueError:
                        auth_outcome = AuthOutcome.NONE

                user_id = state.get("user_id", None)
                if user_id is not None:
                    try:
                        user_id = int(user_id)
                    except (ValueError, TypeError):
                        user_id = None

                event = RequestEvent(
                    request_id=request_id,
                    occurred_at=occurred_at,
                    source_ip=source_ip,
                    path=path_only,
                    normalized_path=norm_path,
                    method=method,
                    status_code=status_code,
                    response_time_ms=duration_ms,
                    auth_outcome=auth_outcome,
                    user_id=user_id,
                )

                # Offload ingestion in threadpool so client response is never blocked or failed
                try:
                    await run_in_threadpool(self.ingest, event)
                except Exception as ingest_exc:
                    ops_logger = get_ops_logger()
                    ops_logger.error(
                        "request_logging_ingest_failure",
                        extra={
                            "extra_fields": {
                                "request_id": request_id,
                                "error": f"{type(ingest_exc).__name__}: {ingest_exc}",
                            }
                        },
                    )
