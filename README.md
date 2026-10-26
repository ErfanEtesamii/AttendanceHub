# AttendHub

Cloud, multi-tenant onboarding portal for Telegram-based attendance systems.

## Local development

1. Copy `.env.example` to `.env` and replace development placeholders where appropriate.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`; backend health is at `http://localhost:8000/api/v1/health`.
4. After migrations, run `python scripts/seed_farazhonar.py` from `backend/` to create the idempotent Faraz Honar seed. Set `FARAZHONAR_OWNER_EMAIL` first if an existing account should own it.

The application refuses to start in production with sample/short secrets or the console OTP provider. No secrets or tokens are stored in browser storage.

## Verification

- Backend: `cd backend; python -m pytest`
- Frontend: `cd frontend; npm ci; npm run lint; npm run typecheck; npm run build`

See `README.fa.md` for Persian setup instructions and `docs/00_DECISIONS.md` for architecture decisions.

## Operations

- Promote an existing account only with `python scripts/create_platform_admin.py owner@example.com`; public registration always creates a regular user.
- The bot status endpoint intentionally reports only readiness, never a token. Dedicated bot tokens are encrypted server-side.
- `docs/INTEGRATION.md` defines the boundary for a future attendance-engine adapter.
