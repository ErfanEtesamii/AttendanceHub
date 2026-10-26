"""Safe persistence helpers for Telegram bot configuration.

This module deliberately never logs or returns a dedicated bot token.  Tokens are
encrypted at rest with a key derived from the deployment encryption secret.
"""

import base64
import hashlib
import re

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings

TOKEN_PATTERN = re.compile(r"^\d{6,12}:[A-Za-z0-9_-]{20,}$")


def _fernet(settings: Settings) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.encryption_key.encode()).digest())
    return Fernet(key)


def validate_dedicated_token(token: str) -> bool:
    """Validate Telegram's token shape without sending it to Telegram."""
    return bool(TOKEN_PATTERN.fullmatch(token))


def encrypt_bot_token(token: str, settings: Settings) -> str:
    return _fernet(settings).encrypt(token.encode()).decode()


def has_decryptable_token(ciphertext: str | None, settings: Settings) -> bool:
    if not ciphertext:
        return False
    try:
        _fernet(settings).decrypt(ciphertext.encode())
    except (InvalidToken, ValueError):
        return False
    return True
