from app.bots import encrypt_bot_token, has_decryptable_token, validate_dedicated_token
from app.config import Settings


def test_dedicated_token_is_validated_and_encrypted() -> None:
    settings = Settings(jwt_secret="x" * 32, encryption_key="y" * 32)
    token = "123456789:abcdefghijklmnopqrstuvwxyz_123"
    assert validate_dedicated_token(token)
    assert not validate_dedicated_token("plain-text-secret")
    ciphertext = encrypt_bot_token(token, settings)
    assert token not in ciphertext
    assert has_decryptable_token(ciphertext, settings)
