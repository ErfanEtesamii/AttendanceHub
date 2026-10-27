from typing import Protocol
from email.message import EmailMessage
import smtplib

from app.config import Settings


class OtpSender(Protocol):
    def send(self, email: str, code: str, purpose: str) -> None: ...


class ConsoleOtpSender:
    def send(self, email: str, code: str, purpose: str) -> None:
        # Development-only: never return this value from an HTTP response.
        print(f"OTP provider=console purpose={purpose} recipient={email} code={code}")


class SmtpOtpSender:
    def __init__(self, settings: Settings) -> None: self.settings = settings
    def send(self, email: str, code: str, purpose: str) -> None:
        message = EmailMessage(); message["From"] = self.settings.smtp_from_email; message["To"] = email; message["Subject"] = "AttendHub verification code"; message.set_content(f"Your verification code is: {code}\nIt expires in 5 minutes.")
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as client:
            client.starttls(); client.login(self.settings.smtp_username, self.settings.smtp_password); client.send_message(message)


def get_otp_sender(settings: Settings) -> OtpSender:
    if settings.otp_provider == "console" and settings.environment != "production":
        return ConsoleOtpSender()
    if settings.otp_provider == "smtp" and settings.smtp_host:
        return SmtpOtpSender(settings)
    raise RuntimeError("No production OTP provider is configured")
