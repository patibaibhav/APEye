"""Database configuration settings (Owner: Anvi).

Reads environment variables according to config-contract.md:
- DATABASE_URL: PostgreSQL database connection string
- DB_POOL_SIZE: Connection pool size (default 5)
"""

import os
from functools import lru_cache

from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/apimonitor",
        )
    )
    db_pool_size: int = Field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Returns cached database settings."""
    return DatabaseSettings()
