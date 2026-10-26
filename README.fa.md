# AttendHub

درگاه ابری و چندشرکتی راه‌اندازی سامانه حضور و غیاب تلگرامی است.

## اجرای محلی

۱. فایل `.env.example` را با نام `.env` کپی کنید.
۲. دستور `docker compose up --build` را اجرا کنید.
۳. رابط در `http://localhost:3000` و سلامت بک‌اند در `http://localhost:8000/api/v1/health` در دسترس است.
۴. پس از migration، برای ساخت شرکت seed فراز هنر از پوشهٔ `backend/` دستور `python scripts/seed_farazhonar.py` را اجرا کنید. برای تعیین مالکِ حساب موجود، ابتدا `FARAZHONAR_OWNER_EMAIL` را تنظیم کنید.

در محیط production، راز کوتاه یا نمونه و Provider کنسولی OTP باعث توقف برنامه می‌شود. هیچ توکن یا رازی در localStorage ذخیره نمی‌شود.

## بررسی کیفیت

- بک‌اند: `cd backend; python -m pytest`
- فرانت‌اند: `cd frontend; npm ci; npm run lint; npm run typecheck; npm run build`

## عملیات

- فقط با `python scripts/create_platform_admin.py owner@example.com` می‌توان حساب موجود را مدیر پلتفرم کرد؛ ثبت‌نام عمومی همیشه نقش کاربر عادی می‌سازد.
- endpoint سلامت بات فقط وضعیت آمادگی را برمی‌گرداند؛ توکن بات اختصاصی رمزنگاری‌شده است و هرگز در پاسخ API یا مرورگر نمایش داده نمی‌شود.
- مرز اتصال آینده با موتور حضور در `docs/INTEGRATION.md` ثبت شده است.
