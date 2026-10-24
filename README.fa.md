# AttendHub

درگاه ابری و چندشرکتی راه‌اندازی سامانه حضور و غیاب تلگرامی است.

## اجرای محلی

۱. فایل `.env.example` را با نام `.env` کپی کنید.
۲. دستور `docker compose up --build` را اجرا کنید.
۳. رابط در `http://localhost:3000` و سلامت بک‌اند در `http://localhost:8000/api/v1/health` در دسترس است.

در محیط production، راز کوتاه یا نمونه و Provider کنسولی OTP باعث توقف برنامه می‌شود. هیچ توکن یا رازی در localStorage ذخیره نمی‌شود.

## بررسی کیفیت

- بک‌اند: `cd backend; python -m pytest`
- فرانت‌اند: `cd frontend; npm ci; npm run lint; npm run typecheck; npm run build`
