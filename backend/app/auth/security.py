"""Password hashing (bcrypt) and JWT helpers.

bcrypt is used directly: passlib is unmaintained and breaks with bcrypt >= 4.1.
Hashes created by the previous passlib-based code (``$2b$...``) stay valid.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings

_BCRYPT_MAX_BYTES = 72

# Used to keep login timing similar for unknown emails.
_DUMMY_HASH = bcrypt.hashpw(b"edurag-dummy-password", bcrypt.gensalt(rounds=12)).decode()


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        raw = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(raw, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def burn_password_check(plain_password: str) -> None:
    """Spend the same time as a real check (unknown-user login path)."""
    verify_password(plain_password, _DUMMY_HASH)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
    )
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
