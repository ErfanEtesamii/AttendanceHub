"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const [message, setMessage] = useState(""); const router = useRouter();
  useEffect(() => { fetch("/api/v1/auth/preferences").then((response) => response.ok ? response.json() : null).then((data) => { if (data) { const locale = document.querySelector<HTMLSelectElement>("[name=locale]"); const theme = document.querySelector<HTMLSelectElement>("[name=theme]"); if (locale) locale.value = data.locale; if (theme) theme.value = data.theme; } }); }, []);
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); const response = await fetch("/api/v1/auth/preferences", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ locale: data.get("locale"), theme: data.get("theme") }) }); setMessage(response.ok ? "تنظیمات ذخیره شد." : "ذخیرهٔ تنظیمات ناموفق بود."); }
  async function logoutAll() { const response = await fetch("/api/v1/auth/logout-all", { method: "POST" }); if (response.ok) router.replace("/login"); else setMessage("خروج از نشست‌ها ناموفق بود."); }
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">تنظیمات حساب</h1><form onSubmit={save} className="mt-6 space-y-4 rounded border p-5"><label className="block">زبان<select name="locale" className="mt-2 block w-full rounded border p-2"><option value="fa">فارسی</option><option value="en">English</option></select></label><label className="block">تم<select name="theme" className="mt-2 block w-full rounded border p-2"><option value="system">خودکار</option><option value="light">روشن</option><option value="dark">تیره</option></select></label><button className="rounded bg-[var(--primary)] px-4 py-2 text-white">ذخیره</button></form><section className="mt-6 rounded border border-red-200 p-5"><h2 className="font-semibold">منطقهٔ خطر</h2><p className="mt-2 text-sm">از همهٔ دستگاه‌ها خارج شوید.</p><button onClick={logoutAll} className="mt-3 rounded border border-red-600 px-4 py-2 text-red-700">خروج از همهٔ نشست‌ها</button></section>{message && <p className="mt-4" aria-live="polite">{message}</p>}</main>;
}
