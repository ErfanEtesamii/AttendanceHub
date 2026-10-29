# Security controls

| OWASP area | Implemented control | Verification | Remaining gap |
| --- | --- | --- | --- |
| Broken access control | Central tenant context, default-deny permissions, active company/membership checks | Backend permission and client-IP tests | Full role×route PostgreSQL integration matrix remains pending. |
| Cryptographic failures | Argon2id passwords, httpOnly cookies, encrypted dedicated bot tokens | Security and bot unit tests | Key rotation/versioning is pending. |
| Injection | Pydantic validation and SQLAlchemy parameterized queries | Schema/unit tests | No independent fuzz suite yet. |
| Insecure design | Tenant-scoped routes, audit logging, invitation expiry | Backend unit tests | Ownership-transfer double confirmation is pending. |
| Security misconfiguration | Production startup validation, explicit Compose secrets, CSP, HSTS | Config tests and Compose interpolation failure | Production CSP nonce/report endpoint remains pending. |
| Identification/authentication | OTP expiry/cooldown, session rotation and refresh reuse invalidation | Auth/security unit tests | Database-backed distributed rate limiting and optional 2FA flow remain pending. |
| Software/data integrity | Alembic migrations and secret scan in CI | Migration head and secret scan | Dependency audit gate needs CI execution. |
| Logging/monitoring | Tenant audit records for sensitive operations | Route-level audit writes | Centralized monitoring/alerting is pending. |
| SSRF | Bot integration is limited to a fixed provider endpoint | Code review | Real Telegram client validation is pending. |

API responses use `no-store`, `nosniff`, frame protection, strict referrer policy, body-size limits, and CSRF origin checks. Secrets must never be committed; run `python scripts/secret_scan.py` before release.
