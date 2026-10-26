# Attendance-engine integration

AttendHub is the onboarding and tenant boundary, not the attendance-command engine.

1. Add a concrete implementation of `AttendanceEngineClient` in `backend/app/engine.py`.
2. Resolve the company from a validated route and membership before calling it; never accept `company_id` from a request body.
3. Pass only the minimum necessary company-scoped data to the engine.
4. Keep the `MockEngineClient` as the development default until the external engine has an authenticated, audited contract.

Telegram bot tokens are never passed through browser APIs. Dedicated tokens are encrypted at rest; shared bots are configured with `SHARED_BOT_USERNAME`.
