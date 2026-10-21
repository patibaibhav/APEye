"""Health check endpoint (Owner: Baibhav).

Follows the API contract:
- GET /api/health (public)
- 200 {status: "ok", database: "ok", version, time}
- 503 with database: "error" if database connectivity fails
- Never exposes secrets, passwords, or connection strings.
"""

from datetime import datetime, timezone
import os
from typing import Callable
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

import app

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
    time: str


def check_database_connectivity() -> bool:
    """Verifies database connectivity with lightweight SELECT 1.

    Catches all exceptions to ensure no secrets or stack traces are leaked.
    """
    try:
        from app.db import session as db_session
        if hasattr(db_session, "engine"):
            from sqlalchemy import text
            with db_session.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        elif hasattr(db_session, "SessionLocal"):
            from sqlalchemy import text
            with db_session.SessionLocal() as session:
                session.execute(text("SELECT 1"))
            return True
        return False
    except Exception:
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "Database unavailable",
        }
    },
)
def get_health(
    response: Response,
    is_db_ok: bool = Depends(check_database_connectivity),
) -> HealthResponse:
    """Returns application health and database connectivity status."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    app_version = getattr(app, "__version__", "0.1.0")

    if not is_db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="ok",
            database="error",
            version=app_version,
            time=now_utc,
        )

    return HealthResponse(
        status="ok",
        database="ok",
        version=app_version,
        time=now_utc,
    )
