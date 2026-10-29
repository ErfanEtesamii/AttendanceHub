"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Overview = { name: string; status: string; member_count: number; attendance_mode: string; bot_configured: boolean };

export default function CompanyAdminPage({ params }: { params: Promise<{ slug: string }> }) {
  const [slug, setSlug] = useState(""); const [overview, setOverview] = useState<Overview | null>(null);
  useEffect(() => { params.then(({ slug: value }) => { setSlug(value); return fetch(`/api/v1/companies/${value}/overview`); }).then((response) => response.ok ? response.json() : null).then(setOverview); }, [params]);
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">پنل مدیریت شرکت</h1>{overview ? <section className="mt-5 grid gap-3 sm:grid-cols-3"><div className="rounded border p-4"><b>{overview.name}</b><p>وضعیت: {overview.status}</p></div><div className="rounded border p-4">اعضای فعال: {overview.member_count}<p>روش حضور: {overview.attendance_mode}</p></div><div className="rounded border p-4">بات: {overview.bot_configured ? "پیکربندی شده" : "نیازمند پیکربندی"}</div></section> : <p className="mt-4">در حال دریافت وضعیت شرکت…</p>}<nav className="mt-6 flex flex-wrap gap-4"><Link href={`/c/${slug}/admin/company`}>اطلاعات شرکت</Link><Link href={`/c/${slug}/admin/members`}>اعضا</Link><Link href={`/c/${slug}/admin/invitations`}>دعوت‌نامه‌ها</Link><Link href={`/c/${slug}/admin/attendance-policy`}>سیاست حضور</Link><Link href={`/c/${slug}/admin/bot`}>اتصال بات</Link><Link href={`/c/${slug}/admin/audit`}>رویدادها</Link><Link href={`/c/${slug}/attendance`}>حضور و غیاب</Link></nav></main>;
}
