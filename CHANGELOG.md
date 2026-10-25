# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Authentication foundation: cookie-only sessions, Argon2id passwords, refresh-token rotation, OTP provider abstraction, password reset path, rate limiting, migrations, and initial auth UI.
- Public landing page and initial about, contact, terms, and privacy pages.
- Public SEO routes and global loading, error, and not-found states.
- Initial company onboarding wizard, multi-tenant company models, memberships, and attendance-policy API.
- CIDR/IP and location-radius attendance policy primitives with boundary tests.
- Tenant-scoped attendance-policy test endpoint and initial administrator test screen.

## [0.1.0] - 2026-10-24

### Added
- Phase 1 monorepo scaffold with Next.js, FastAPI, PostgreSQL, Docker Compose, health checks, startup validation, i18n message catalogues, theme foundation, lint/type/test commands, and CI.
