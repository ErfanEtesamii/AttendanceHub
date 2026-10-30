"""Authentication primitives. Tokens are issued only for httpOnly cookies."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow, token_urlsafe

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings

_password_hasher = PasswordHasher()


def is_strong_password(password: str) -> bool:
    return (
        8 <= len(password) <= 128
        and any(character.islower() for character in password)
        and any(character.isupper() for character in password)
        and any(character.isdigit() for character in password)
        and any(not character.isalnum() for character in password)
    )


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


def issue_login_challenge(subject: str, token_version: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": subject, "ver": token_version, "purpose": "login_2fa", "iat": now, "exp": now + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_login_challenge(token: str, settings: Settings) -> dict[str, object] | None:
    claims = decode_access_token(token, settings)
    return claims if claims and claims.get("purpose") == "login_2fa" else None


def decode_access_token(token: str, settings: Settings) -> dict[str, object] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def new_refresh_token() -> str:
    return token_urlsafe(48)


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def new_otp() -> str:
    return f"{randbelow(1_000_000):06d}"
