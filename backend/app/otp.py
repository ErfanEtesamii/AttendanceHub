from typing import Protocol

from app.config import Settings


class OtpSender(Protocol):
    def send(self, email: str, code: str, purpose: str) -> None: ...


class ConsoleOtpSender:
    def send(self, email: str, code: str, purpose: str) -> None:
        # Development-only: never return this value from an HTTP response.
        print(f"OTP provider=console purpose={purpose} recipient={email} code={code}")


def get_otp_sender(settings: Settings) -> OtpSender:
    if settings.otp_provider == "console" and settings.environment != "production":
        return ConsoleOtpSender()
    raise RuntimeError("No production OTP provider is configured")
