from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_hasher = PasswordHash.recommended()

# Verified against when the email is unknown, so timing doesn't reveal which emails exist.
DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(password, hashed)
    except Exception:
        # Malformed hash (for example the dev user's "!disabled" placeholder)
        return False


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    minutes = settings.jwt_expire_minutes if expires_minutes is None else expires_minutes
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> int | None:
    """Return the user id from a valid token, or None for any invalid one."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None