"""Users management API routes (Owner: Anvi).

Endpoints:
- GET /api/users (ADMIN only)
- POST /api/users (ADMIN only)
- PATCH /api/users/{id} (ADMIN only)
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.common_params import PaginationParams
from app.auth.dependencies import require_role
from app.auth.security import hash_password
from app.core.errors import ForbiddenError, NotFoundError, UsernameTakenError
from app.db.repositories import user_repository
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserRead, UserUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(tags=["users"])


@router.get("", response_model=PaginatedResponse[UserRead], status_code=status.HTTP_200_OK)
def list_users(
    pagination: PaginationParams = Depends(),
    admin_user: Any = Depends(require_role("ADMIN")),
    session: Session = Depends(get_db),
) -> PaginatedResponse[UserRead]:
    """Lists registered users with pagination (ADMIN role required)."""
    items, total = user_repository.list_users(
        session=session,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return PaginatedResponse(
        items=[UserRead.model_validate(u) for u in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total,
        total_pages=total_pages,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_new_user(
    body: UserCreate,
    admin_user: Any = Depends(require_role("ADMIN")),
    session: Session = Depends(get_db),
) -> UserRead:
    """Creates a new user account (ADMIN role required, password min 12 characters)."""
    existing = user_repository.get_user_by_username(session, body.username)
    if existing is not None:
        raise UsernameTakenError("Username already exists")

    pwd_hash = hash_password(body.password)
    user = user_repository.create_user(
        session=session,
        username=body.username,
        password_hash=pwd_hash,
        role=body.role,
    )
    session.commit()
    return UserRead.model_validate(user)


@router.patch("/{id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_user_profile(
    id: int,
    body: UserUpdate,
    admin_user: Any = Depends(require_role("ADMIN")),
    session: Session = Depends(get_db),
) -> UserRead:
    """Updates user active status or role (ADMIN only, prevents self-deactivation)."""
    admin_id = getattr(admin_user, "id", None) or (
        admin_user.get("id") if isinstance(admin_user, dict) else None
    )
    if admin_id == id and body.is_active is False:
        raise ForbiddenError("Administrators cannot deactivate themselves")

    user = user_repository.get_user_by_id(session, id)
    if user is None:
        raise NotFoundError(f"User with ID {id} not found")

    updated = user_repository.update_user(
        session=session,
        user_id=id,
        is_active=body.is_active,
        role=body.role,
    )
    session.commit()
    return UserRead.model_validate(updated)
