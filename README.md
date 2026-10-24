# AttendHub

Cloud, multi-tenant onboarding portal for Telegram-based attendance systems.

## Local development

1. Copy `.env.example` to `.env` and replace development placeholders where appropriate.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`; backend health is at `http://localhost:8000/api/v1/health`.

The application refuses to start in production with sample/short secrets or the console OTP provider. No secrets or tokens are stored in browser storage.

## Verification

- Backend: `cd backend; python -m pytest`
- Frontend: `cd frontend; npm ci; npm run lint; npm run typecheck; npm run build`

See `README.fa.md` for Persian setup instructions and `docs/00_DECISIONS.md` for architecture decisions.
