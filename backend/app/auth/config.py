"""Authentication and JWT configuration settings (Owner: Anvi)."""

import os
from functools import lru_cache

from pydantic import BaseModel, Field


class AuthSettings(BaseModel):
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv(
            "JWT_SECRET_KEY",
            "replace-with-a-random-secret-key-at-least-32-chars-long",
        )
    )
    jwt_expire_minutes: int = Field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    )
    admin_username: str = Field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin"))
    admin_password: str = Field(
        default_factory=lambda: os.getenv("ADMIN_PASSWORD", "change_this_admin_password_123")
    )


@lru_cache()
def get_auth_settings() -> AuthSettings:
    """Returns cached authentication settings."""
    return AuthSettings()
