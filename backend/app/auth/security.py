"""Security utilities: bcrypt password hashing and JWT token management (Owner: Anvi)."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from app.auth.config import get_auth_settings
from app.core.errors import TokenExpiredError, TokenInvalidError


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, datetime]:
    """Generates a signed JWT access token and its expiration timestamp."""
    settings = get_auth_settings()
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    expires_at = now + delta

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token, mapping errors to contract-defined exceptions."""
    settings = get_auth_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Token has expired") from exc
    except (jwt.InvalidTokenError, jwt.PyJWTError) as exc:
        raise TokenInvalidError("Invalid token") from exc
