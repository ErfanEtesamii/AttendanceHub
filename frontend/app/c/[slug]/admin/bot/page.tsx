"use client";

import { FormEvent, useEffect, useState } from "react";

type BotStatus = { mode: string; username: string | null; dedicated_configured: boolean };

export default function BotPage({ params }: { params: Promise<{ slug: string }> }) {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => { params.then(({ slug }) => fetch(`/api/v1/companies/${slug}/bot`).then((r) => r.ok ? r.json() : null).then(setStatus)); }, [params]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const slug = (await params).slug; const form = new FormData(event.currentTarget);
    const response = await fetch(`/api/v1/companies/${slug}/bot`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: form.get("mode"), username: form.get("username") || null, dedicated_token: form.get("dedicated_token") || null }) });
    setMessage(response.ok ? "تنظیمات بات بدون ذخیرهٔ توکن در مرورگر ثبت شد." : "تنظیمات ثبت نشد؛ اطلاعات بات را بررسی کنید.");
    if (response.ok) setStatus((current) => ({ mode: String(form.get("mode")), username: String(form.get("username")) || null, dedicated_configured: String(form.get("mode")) === "dedicated" || current?.dedicated_configured === true }));
  }
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">اتصال بات تلگرام</h1><p className="mt-2 text-sm text-slate-600">برای بات اختصاصی، توکن فقط هنگام ثبت به سرور ارسال و رمزنگاری می‌شود و دیگر نمایش داده نخواهد شد.</p><form onSubmit={save} className="mt-6 space-y-4 rounded border p-5"><label className="block">روش اتصال<select name="mode" defaultValue={status?.mode ?? "shared"} className="mt-2 block w-full rounded border p-2"><option value="shared">بات مشترک پلتفرم</option><option value="dedicated">بات اختصاصی شرکت</option></select></label><label className="block">نام کاربری بات (اختیاری)<input name="username" defaultValue={status?.username ?? ""} dir="ltr" className="mt-2 w-full rounded border p-2" placeholder="AttendanceBot" /></label><label className="block">توکن بات اختصاصی<input name="dedicated_token" type="password" dir="ltr" autoComplete="off" className="mt-2 w-full rounded border p-2" placeholder="فقط برای حالت اختصاصی" /></label><button className="rounded bg-[var(--primary)] px-4 py-2 text-white">ذخیرهٔ امن</button></form>{status && <p className="mt-4" aria-live="polite">وضعیت فعلی: {status.mode === "dedicated" ? (status.dedicated_configured ? "بات اختصاصی آماده است" : "بات اختصاصی هنوز کامل نشده") : "بات مشترک"}</p>}{message && <p className="mt-3" aria-live="polite">{message}</p>}</main>;
}
