from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Production configuration fails closed."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AttendHub"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://attendhub:attendhub_local_password@postgres:5432/attendhub"
    jwt_secret: str = Field(min_length=32)
    encryption_key: str = Field(min_length=32)
    cors_origins: str = "http://localhost:3000"
    otp_provider: str = "console"
    shared_bot_username: str | None = None
    farazhonar_owner_email: str | None = None
    farazhonar_allowed_cidr: str = "192.168.10.0/24"
    app_public_url: str = "http://localhost:3000"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    trusted_proxies: str = ""

    @property
    def trusted_proxy_networks(self) -> list[str]:
        return [item.strip() for item in self.trusted_proxies.split(",") if item.strip()]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        if value not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        return value

    @model_validator(mode="after")
    def reject_unsafe_production_configuration(self) -> "Settings":
        if self.environment != "production":
            return self
        unsafe_markers = ("change-me", "replace-with", "example", "sample", "local_password")
        for name in ("jwt_secret", "encryption_key"):
            value = getattr(self, name).lower()
            if len(value) < 32 or any(marker in value for marker in unsafe_markers):
                raise ValueError(f"{name.upper()} must be a strong non-sample secret in production")
        if self.otp_provider == "console":
            raise ValueError("OTP_PROVIDER=console is not allowed in production")
        if self.otp_provider == "smtp" and not all((self.smtp_host, self.smtp_username, self.smtp_password, self.smtp_from_email)):
            raise ValueError("SMTP configuration is required when OTP_PROVIDER=smtp")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
