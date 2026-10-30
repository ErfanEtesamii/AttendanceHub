"""Authentication checks against a migrated PostgreSQL test database."""

import os
from uuid import uuid4

import pytest


def test_register_verify_session_and_logout_all(monkeypatch: pytest.MonkeyPatch) -> None:
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL must point to a migrated PostgreSQL database")

    from fastapi.testclient import TestClient
    from sqlalchemy import delete, select

    from app.database import SessionLocal
    from app.main import app
    from app.models import Company, OtpChallenge, User
    import app.routers.auth as auth_router

    captured: list[str] = []

    class Sender:
        def send(self, email: str, code: str, purpose: str) -> None:
            captured.append(code)

    monkeypatch.setattr(auth_router, "get_otp_sender", lambda settings: Sender())
    monkeypatch.setattr(auth_router, "resolve_client_ip", lambda *args: "127.0.0.1")
    suffix = uuid4().hex[:16]
    email = f"test-{suffix}@example.com"
    username = f"test_{suffix}"
    slug = f"test-{suffix}"

    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            registered = client.post(
                "/api/v1/auth/register",
                json={"name": "Test User", "username": username, "email": email, "password": "ValidPass1!"},
            )
            assert registered.status_code == 201, registered.text
            assert len(captured) == 1

            verified = client.post(
                "/api/v1/auth/otp/verify",
                json={"email": email, "purpose": "verify_email", "code": captured[0]},
            )
            assert verified.status_code == 200, verified.text
            assert client.get("/api/v1/auth/me").status_code == 200

            company = client.post(
                "/api/v1/companies",
                headers={"origin": "http://localhost:3000"},
                json={"name": "Zero Point", "slug": slug, "mode": "location", "latitude": 0, "longitude": 0, "radius_meters": 20},
            )
            assert company.status_code == 201, company.text
            policy = client.get(f"/api/v1/companies/{slug}/attendance-policy")
            assert policy.status_code == 200, policy.text
            assert float(policy.json()["latitude"]) == 0
            duplicate = client.post(
                "/api/v1/companies",
                headers={"origin": "http://localhost:3000"},
                json={"name": "Duplicate", "slug": slug, "mode": "ip", "allowed_cidr": "192.0.2.0/24"},
            )
            assert duplicate.status_code == 409, duplicate.text

            enabled = client.patch(
                "/api/v1/auth/two-factor",
                headers={"origin": "http://localhost:3000"},
                json={"enabled": True, "current_password": "ValidPass1!"},
            )
            assert enabled.status_code == 204, enabled.text
            assert client.get("/api/v1/auth/me").status_code == 401
            login = client.post("/api/v1/auth/login", json={"identifier": username, "password": "ValidPass1!"})
            assert login.status_code == 200, login.text
            assert login.json()["status"] == "two_factor_required"
            assert client.get("/api/v1/auth/me").status_code == 401
            two_factor_verified = client.post(
                "/api/v1/auth/otp/verify",
                json={"email": email, "purpose": "login_2fa", "code": captured[-1], "login_token": login.json()["login_token"]},
            )
            assert two_factor_verified.status_code == 200, two_factor_verified.text
            assert client.get("/api/v1/auth/me").status_code == 200

            logged_out = client.post("/api/v1/auth/logout-all", headers={"origin": "http://localhost:3000"})
            assert logged_out.status_code == 204, logged_out.text
            assert client.get("/api/v1/auth/me").status_code == 401
    finally:
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.email == email))
            company = session.scalar(select(Company).where(Company.slug == slug))
            if company is not None:
                session.delete(company)
            session.execute(delete(OtpChallenge).where(OtpChallenge.email == email))
            if user is not None:
                session.delete(user)
            session.commit()
