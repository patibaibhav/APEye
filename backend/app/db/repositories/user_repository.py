"""User repository implementing parameterized SQLAlchemy queries (Owner: Anvi)."""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.user import User


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Retrieves a single user by primary key ID."""
    stmt = select(User).where(User.id == user_id)
    return session.execute(stmt).scalar_one_or_none()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Retrieves a single user by exact unique username."""
    stmt = select(User).where(User.username == username)
    return session.execute(stmt).scalar_one_or_none()


def create_user(session: Session, username: str, password_hash: str, role: str) -> User:
    """Creates and persists a new user record."""
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def update_user(
    session: Session,
    user_id: int,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    last_login_at: Optional[datetime] = None,
) -> Optional[User]:
    """Updates user attributes and flushes changes."""
    user = get_user_by_id(session, user_id)
    if user is None:
        return None

    if is_active is not None:
        user.is_active = is_active
    if role is not None:
        user.role = role
    if last_login_at is not None:
        user.last_login_at = last_login_at

    session.flush()
    return user


def list_users(session: Session, offset: int = 0, limit: int = 25) -> Tuple[List[User], int]:
    """Lists users with pagination sorted by id ascending, returning items and total count."""
    count_stmt = select(func.count(User.id))
    total = session.execute(count_stmt).scalar() or 0

    stmt = select(User).order_by(User.id.asc()).offset(offset).limit(limit)
    items = list(session.execute(stmt).scalars().all())

    return items, total


def count_users(session: Session) -> int:
    """Returns total number of users."""
    stmt = select(func.count(User.id))
    return session.execute(stmt).scalar() or 0
