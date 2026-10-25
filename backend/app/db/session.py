"""SQLAlchemy session management and database engine (Owner: Anvi).

Provides:
- engine: SQLAlchemy Engine instance configured with safe connection pooling
- SessionLocal: scoped sessionmaker factory
- get_db(): FastAPI dependency for yielding request-scoped database sessions
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.config import get_db_settings

settings = get_db_settings()

# Configure engine with safe connection pooling and pre-ping to detect dropped connections
# Notice: create_engine does not initiate a connection upon creation, ensuring safe imports
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated database session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for background services and scripts with auto-commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

