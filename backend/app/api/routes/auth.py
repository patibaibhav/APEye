"""Auth API routes (Owner: Anvi).

Endpoints:
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.auth.security import create_access_token, verify_password
from app.core.errors import InvalidCredentialsError
from app.db.models.user import User
from app.db.repositories import user_repository
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, UserRead, UserSummary
from app.schemas.common import AuthOutcome

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    request: Request,
    body: LoginRequest,
    session: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticates username and password, returns signed JWT access token and user metadata."""
    user = user_repository.get_user_by_username(session, body.username)

    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        request.state.auth_outcome = AuthOutcome.LOGIN_FAILED
        raise InvalidCredentialsError("Invalid username or password")

    # Update last login timestamp
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    session.commit()

    # Set request state for middleware
    request.state.auth_outcome = AuthOutcome.LOGIN_SUCCESS
    request.state.user_id = user.id

    token, expires_at = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        user=UserSummary(
            id=user.id,
            username=user.username,
            role=user.role,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    """Stateless client-side logout acknowledging session termination."""
    return None


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    user: User = Depends(require_user),
) -> UserRead:
    """Returns currently authenticated user profile."""
    return UserRead.model_validate(user)
