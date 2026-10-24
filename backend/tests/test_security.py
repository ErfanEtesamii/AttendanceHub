from app.config import Settings
from app.security import hash_password, issue_access_token, new_otp, new_refresh_token, token_digest, verify_password
from app.otp import get_otp_sender


def test_password_is_argon2id_and_verifiable() -> None:
    password_hash = hash_password("a-long-and-unique-password")
    assert password_hash.startswith("$argon2id$")
    assert verify_password("a-long-and-unique-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_never_contains_password() -> None:
    token = issue_access_token("user-id", 0, Settings(jwt_secret="a" * 32, encryption_key="b" * 32))
    assert "password" not in token
    assert len(new_refresh_token()) >= 32
    assert token_digest("value") != "value"


def test_otp_is_always_six_numeric_digits() -> None:
    assert new_otp().isdigit() and len(new_otp()) == 6


def test_console_sender_is_development_only() -> None:
    assert get_otp_sender(Settings(jwt_secret="a" * 32, encryption_key="b" * 32)).__class__.__name__ == "ConsoleOtpSender"
