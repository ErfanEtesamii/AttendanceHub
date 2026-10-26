"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Company = { name: string; slug: string; role: string };

export default function DashboardPage() {
  const [companies, setCompanies] = useState<Company[] | null>(null);
  useEffect(() => { fetch("/api/v1/companies").then((response) => response.ok ? response.json() : []).then(setCompanies).catch(() => setCompanies([])); }, []);
  if (companies === null) return <main className="p-8" aria-busy="true">در حال دریافت شرکت‌ها…</main>;
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">داشبورد</h1>{companies.length === 0 ? <section className="mt-6 rounded border p-6"><h2 className="text-lg font-semibold">هنوز شرکتی ندارید</h2><p className="mt-2">برای راه‌اندازی حضور و غیاب، نخستین شرکت خود را ثبت کنید.</p><Link className="mt-5 inline-block rounded bg-[var(--primary)] px-4 py-2 text-white" href="/dashboard/companies/new">ثبت شرکت</Link></section> : <><p className="mt-3">شرکت موردنظر را برای ورود به پنل انتخاب کنید.</p><ul className="mt-6 grid gap-4 sm:grid-cols-2">{companies.map((company) => <li className="rounded border p-5" key={company.slug}><h2 className="font-semibold">{company.name}</h2><p className="mt-1 text-sm text-slate-600">نقش: {company.role}</p><Link className="mt-4 inline-block text-[var(--primary)] underline" href={`/c/${company.slug}/admin`}>ورود به پنل شرکت</Link></li>)}</ul><Link className="mt-6 inline-block rounded border px-4 py-2" href="/dashboard/companies/new">ثبت شرکت جدید</Link></>}</main>;
}
