"""Unit tests for RequestLoggingMiddleware."""

import asyncio
from typing import List

from app.middleware.request_logging import RequestLoggingMiddleware
from app.schemas.common import AuthOutcome
from app.schemas.detection import RequestEvent


def create_asgi_scope(
    path: str = "/api/users",
    method: str = "GET",
    scope_type: str = "http",
    client_ip: str = "192.168.1.100",
    headers: list | None = None,
) -> dict:
    default_headers = [
        (b"host", b"localhost:8000"),
        (b"authorization", b"Bearer secret-token-not-to-be-logged"),
    ]
    if headers:
        default_headers.extend(headers)

    return {
        "type": scope_type,
        "method": method,
        "path": path,
        "headers": default_headers,
        "client": (client_ip, 54321),
        "state": {},
    }


async def dummy_receive():
    return {"type": "http.request"}


async def dummy_send(msg):
    pass


def test_non_http_scope_passthrough():
    async def run_test():
        app_called = False
        captured_events: List[RequestEvent] = []

        async def dummy_app(scope, receive, send):
            nonlocal app_called
            app_called = True

        middleware = RequestLoggingMiddleware(app=dummy_app, ingest=captured_events.append)
        scope = {"type": "lifespan"}
        await middleware(scope, dummy_receive, dummy_send)

        assert app_called is True
        assert len(captured_events) == 0

    asyncio.run(run_test())


def test_health_and_non_api_paths_ignored():
    async def run_test():
        captured_events: List[RequestEvent] = []

        async def ok_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok", "more_body": False})

        middleware = RequestLoggingMiddleware(app=ok_app, ingest=captured_events.append)

        # 1. /api/health must be ignored by default
        scope_health = create_asgi_scope(path="/api/health")
        await middleware(scope_health, dummy_receive, dummy_send)
        assert len(captured_events) == 0

        # 2. Non-/api path must be ignored
        scope_root = create_asgi_scope(path="/index.html")
        await middleware(scope_root, dummy_receive, dummy_send)
        assert len(captured_events) == 0

    asyncio.run(run_test())


def test_api_request_logging_and_header_injection():
    async def run_test():
        captured_events: List[RequestEvent] = []
        sent_messages = []

        async def api_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b'{"status": "ok"}', "more_body": False})

        middleware = RequestLoggingMiddleware(app=api_app, ingest=captured_events.append)
        scope = create_asgi_scope(path="/api/logs/999?query=secret_value")

        async def mock_send(message):
            sent_messages.append(message)

        await middleware(scope, dummy_receive, mock_send)

        # Verify X-Request-ID was injected into response headers
        start_msg = sent_messages[0]
        headers_dict = dict(start_msg["headers"])
        assert b"x-request-id" in headers_dict
        injected_req_id = headers_dict[b"x-request-id"].decode("ascii")

        # Verify captured event fields
        assert len(captured_events) == 1
        event = captured_events[0]
        assert event.request_id == injected_req_id
        assert event.path == "/api/logs/999"  # Query string stripped!
        assert "query=secret_value" not in event.path
        assert event.normalized_path == "/api/logs/{id}"  # Normalized ID
        assert event.status_code == 200
        assert event.response_time_ms >= 0
        assert event.source_ip == "192.168.1.100"
        assert event.auth_outcome == AuthOutcome.NONE
        assert event.user_id is None

    asyncio.run(run_test())


def test_auth_state_handoff_and_streaming():
    async def run_test():
        captured_events: List[RequestEvent] = []

        async def streaming_app(scope, receive, send):
            # Anvi's auth middleware sets request.state.auth_outcome and user_id
            scope["state"]["auth_outcome"] = AuthOutcome.AUTHENTICATED
            scope["state"]["user_id"] = 77

            await send({"type": "http.response.start", "status": 200, "headers": []})
            # Simulate streaming chunk 1
            await asyncio.sleep(0.01)
            await send({"type": "http.response.body", "body": b"chunk1", "more_body": True})
            # Simulate streaming chunk 2 (final)
            await asyncio.sleep(0.01)
            await send({"type": "http.response.body", "body": b"chunk2", "more_body": False})

        middleware = RequestLoggingMiddleware(app=streaming_app, ingest=captured_events.append)
        scope = create_asgi_scope(path="/api/exports/logs.csv")
        await middleware(scope, dummy_receive, dummy_send)

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event.auth_outcome == AuthOutcome.AUTHENTICATED
        assert event.user_id == 77
        assert event.response_time_ms >= 10  # Duration covered both stream chunks!

    asyncio.run(run_test())


def test_app_exception_records_500_and_reraises():
    async def run_test():
        captured_events: List[RequestEvent] = []

        async def failing_app(scope, receive, send):
            raise RuntimeError("Unexpected internal crash")

        middleware = RequestLoggingMiddleware(app=failing_app, ingest=captured_events.append)
        scope = create_asgi_scope(path="/api/unstable/endpoint")

        try:
            await middleware(scope, dummy_receive, dummy_send)
            assert False, "Should have re-raised RuntimeError"
        except RuntimeError as exc:
            assert str(exc) == "Unexpected internal crash"

        # Event must still be captured with status 500
        assert len(captured_events) == 1
        assert captured_events[0].status_code == 500

    asyncio.run(run_test())


def test_ingest_failure_never_affects_client_response():
    async def run_test():
        def exploding_ingest(event: RequestEvent):
            raise ConnectionError("PostgreSQL database connection lost during ingest")

        response_received = False

        async def ok_app(scope, receive, send):
            nonlocal response_received
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"success", "more_body": False})
            response_received = True

        middleware = RequestLoggingMiddleware(app=ok_app, ingest=exploding_ingest)
        scope = create_asgi_scope(path="/api/critical/action")

        # Ingestion failure must be caught and logged, NEVER failing the client!
        await middleware(scope, dummy_receive, dummy_send)
        assert response_received is True

    asyncio.run(run_test())
