import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_sample_secrets() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="replace-with-a-random-secret-of-at-least-32-characters",
            encryption_key="a" * 32,
            otp_provider="smtp",
        )


def test_production_rejects_console_otp() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="a" * 32,
            encryption_key="b" * 32,
            otp_provider="console",
        )


def test_cors_origins_are_normalized() -> None:
    settings = Settings(jwt_secret="a" * 32, encryption_key="b" * 32, cors_origins=" http://a.test ,http://b.test ")
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]
