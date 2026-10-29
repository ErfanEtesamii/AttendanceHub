"use client";

import { FormEvent, useEffect, useState } from "react";

type Company = { name: string; name_en: string | null; industry: string | null; city: string | null; phone: string | null };

export default function CompanyPage({ params }: { params: Promise<{ slug: string }> }) {
  const [company, setCompany] = useState<Company | null>(null); const [message, setMessage] = useState("");
  useEffect(() => { params.then(({ slug }) => fetch(`/api/v1/companies/${slug}`).then((response) => response.ok ? response.json() : null).then(setCompany)); }, [params]);
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const slug = (await params).slug; const data = new FormData(event.currentTarget); const response = await fetch(`/api/v1/companies/${slug}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(data)) }); setMessage(response.ok ? "اطلاعات شرکت ذخیره شد." : "ذخیره‌سازی ناموفق بود."); }
  if (!company) return <main className="p-8" aria-busy="true">در حال دریافت اطلاعات شرکت…</main>;
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">اطلاعات شرکت</h1><form onSubmit={save} className="mt-6 space-y-4 rounded border p-5"><label className="block">نام فارسی<input required name="name" defaultValue={company.name} className="mt-2 w-full rounded border p-2" /></label><label className="block">نام انگلیسی<input name="name_en" defaultValue={company.name_en ?? ""} className="mt-2 w-full rounded border p-2" /></label><label className="block">صنعت<input name="industry" defaultValue={company.industry ?? ""} className="mt-2 w-full rounded border p-2" /></label><label className="block">شهر<input name="city" defaultValue={company.city ?? ""} className="mt-2 w-full rounded border p-2" /></label><label className="block">تلفن<input name="phone" dir="ltr" defaultValue={company.phone ?? ""} className="mt-2 w-full rounded border p-2" /></label><button className="rounded bg-[var(--primary)] px-4 py-2 text-white">ذخیره</button></form>{message && <p className="mt-4" aria-live="polite">{message}</p>}</main>;
}
