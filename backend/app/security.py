"""Authentication primitives. Tokens are issued only for httpOnly cookies."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow, token_urlsafe

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def issue_access_token(subject: str, token_version: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "ver": token_version, "iat": now, "exp": now + timedelta(minutes=15)}, settings.jwt_secret, algorithm="HS256")


def new_refresh_token() -> str:
    return token_urlsafe(48)


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def new_otp() -> str:
    return f"{randbelow(1_000_000):06d}"
