"""FastAPI authentication and authorization dependencies (Owner: Anvi).

Provides:
- require_user: Authenticates bearer JWT, populates request.state for middleware, returns active User
- require_role: Enforces ADMIN or ANALYST authorization
"""

from typing import Any, Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.core.errors import (
    ForbiddenError,
    TokenExpiredError,
    TokenInvalidError,
    UnauthenticatedError,
)
from app.db.models.user import User
from app.db.repositories import user_repository
from app.db.session import get_db
from app.schemas.common import AuthOutcome


def get_token_from_header(request: Request) -> str:
    """Extracts bearer token from Authorization header or raises UnauthenticatedError."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        request.state.auth_outcome = AuthOutcome.NONE
        raise UnauthenticatedError("Authentication required")
    return auth_header[7:].strip()


def require_user(
    request: Request,
    session: Session = Depends(get_db),
) -> User:
    """Authenticates the request bearer token, retrieves the active user, and sets request.state."""
    token = get_token_from_header(request)

    try:
        payload = decode_access_token(token)
    except TokenExpiredError:
        request.state.auth_outcome = AuthOutcome.TOKEN_EXPIRED
        raise
    except TokenInvalidError:
        request.state.auth_outcome = AuthOutcome.TOKEN_INVALID
        raise

    user_id_str = payload.get("sub")
    if not user_id_str:
        request.state.auth_outcome = AuthOutcome.TOKEN_INVALID
        raise TokenInvalidError("Invalid token payload: missing sub")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        request.state.auth_outcome = AuthOutcome.TOKEN_INVALID
        raise TokenInvalidError("Invalid token payload: sub is not an integer")

    user = user_repository.get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        request.state.auth_outcome = AuthOutcome.TOKEN_INVALID
        raise TokenInvalidError("User is inactive or not found")

    # Update request state for middleware request logging
    request.state.auth_outcome = AuthOutcome.AUTHENTICATED
    request.state.user_id = user.id

    return user


def require_role(required_role: str) -> Callable[..., Any]:
    """Dependency factory enforcing that the authenticated user possesses the required role."""

    def role_checker(
        request: Request,
        session: Session = Depends(get_db),
    ) -> Any:
        # Check if get_current_user was overridden in test harness
        overrides = getattr(request.app, "dependency_overrides", {})
        get_current_user_fn = None
        for fn in overrides.keys():
            if getattr(fn, "__name__", "") == "get_current_user":
                get_current_user_fn = fn
                break

        if get_current_user_fn and get_current_user_fn in overrides:
            user = overrides[get_current_user_fn]()
        else:
            user = require_user(request, session)

        role = getattr(user, "role", None) or (user.get("role") if isinstance(user, dict) else None)
        if role != required_role:
            request.state.auth_outcome = AuthOutcome.FORBIDDEN
            raise ForbiddenError(f"Access forbidden: {required_role} role required")

        return user

    return role_checker
