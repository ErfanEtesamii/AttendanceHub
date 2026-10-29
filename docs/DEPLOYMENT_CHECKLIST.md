# Production deployment checklist

- [ ] Set strong, unique `JWT_SECRET` and `ENCRYPTION_KEY` values (at least 32 characters).
- [ ] Configure a real OTP provider; `OTP_PROVIDER=console` is rejected in production.
- [ ] Set the public `CORS_ORIGINS`, `APP_PUBLIC_URL`, trusted reverse proxy and HTTPS termination.
- [ ] Run `alembic upgrade head`, then `python scripts/seed_farazhonar.py` if the default tenant is wanted.
- [ ] Run backend tests, frontend lint/typecheck/build and the CI secret scan.
- [ ] Verify registration → OTP → company onboarding and invitation acceptance on a production-like environment.
- [ ] Confirm API responses carry security headers and cross-origin state-changing requests return 403.
- [ ] Confirm Docker Desktop/daemon is running before `docker compose up --build`; the Compose file intentionally fails without explicit JWT/encryption secrets.
- [ ] Verify PostgreSQL backup and restore procedures before production traffic, and rotate JWT/encryption/SMTP secrets on a defined schedule.
