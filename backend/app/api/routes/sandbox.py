"""Sandbox endpoints for test traffic generation (Owner: Baibhav).

Follows the API Contract and Blueprint:
- Gated by ENABLE_SANDBOX (returns 404 when disabled)
- GET /api/sandbox/ping (public) -> 200 {"ok": true}
- GET /api/sandbox/protected (ANY role: ADMIN or ANALYST) -> 200 {"ok": true}
- GET /api/sandbox/admin-only (ADMIN role only) -> 200 {"ok": true}
- Integrates with Anvi's auth dependencies when available.
"""

from typing import Any, Callable, Tuple
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import ForbiddenError, NotFoundError, UnauthenticatedError
from app.schemas.common import AuthOutcome

router = APIRouter(tags=["sandbox"])


class SandboxResponse(BaseModel):
    ok: bool = True


def verify_sandbox_enabled(request: Request, settings: Settings = Depends(get_settings)) -> None:
    """Ensures sandbox routes are only accessible when ENABLE_SANDBOX is enabled."""
    cfg = getattr(request.app.state, "settings", settings)
    if not cfg.enable_sandbox:
        raise NotFoundError("Sandbox endpoints are disabled in this environment")


# Resolve auth dependencies from Anvi's auth module if present, or define strict stubs
try:
    from app.auth.dependencies import require_role as anvi_require_role
    from app.auth.dependencies import require_user as anvi_require_user

    def get_current_user(request: Request, user: Any = Depends(anvi_require_user)) -> Any:
        return user

    def get_admin_user(request: Request, user: Any = Depends(anvi_require_role("ADMIN"))) -> Any:
        return user

except ImportError:
    # Strict fallback seams: Default to secure rejection (never bypass security)
    def get_current_user(request: Request) -> Any:
        """Dependency seam requiring authenticated user (ANY role: ADMIN or ANALYST)."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            request.state.auth_outcome = AuthOutcome.NONE
            raise UnauthenticatedError("Authentication credentials were not provided")
        # In the absence of Anvi's JWT verification engine, raw header cannot be verified
        request.state.auth_outcome = AuthOutcome.TOKEN_INVALID
        raise UnauthenticatedError("Invalid or unverified authentication token")

    def get_admin_user(request: Request, user: Any = Depends(get_current_user)) -> Any:
        """Dependency seam requiring ADMIN role."""
        role = getattr(user, "role", None) or (user.get("role") if isinstance(user, dict) else None)
        if role != "ADMIN":
            request.state.auth_outcome = AuthOutcome.FORBIDDEN
            raise ForbiddenError("Administrator access required")
        return user


@router.get(
    "/ping",
    response_model=SandboxResponse,
    dependencies=[Depends(verify_sandbox_enabled)],
)
def sandbox_ping() -> SandboxResponse:
    """Public sandbox probe endpoint for traffic generation."""
    return SandboxResponse(ok=True)


@router.get(
    "/protected",
    response_model=SandboxResponse,
    dependencies=[Depends(verify_sandbox_enabled)],
)
def sandbox_protected(user: Any = Depends(get_current_user)) -> SandboxResponse:
    """Protected sandbox endpoint accessible to any authenticated user (ADMIN or ANALYST)."""
    return SandboxResponse(ok=True)


@router.get(
    "/admin-only",
    response_model=SandboxResponse,
    dependencies=[Depends(verify_sandbox_enabled)],
)
def sandbox_admin_only(user: Any = Depends(get_admin_user)) -> SandboxResponse:
    """Protected sandbox endpoint accessible exclusively to administrators."""
    return SandboxResponse(ok=True)
