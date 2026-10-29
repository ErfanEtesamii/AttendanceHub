"use client";

import { useEffect, useState } from "react";

type Company = { name: string; slug: string; timezone: string; status: string };

export default function PlatformPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { fetch("/api/v1/platform/companies").then(async (response) => { if (!response.ok) throw new Error(); return response.json(); }).then(setCompanies).catch(() => setError("دسترسی مدیر پلتفرم لازم است.")); }, []);
  async function toggle(company: Company) { const status = company.status === "active" ? "suspended" : "active"; const response = await fetch(`/api/v1/platform/companies/${company.slug}/status`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) }); if (response.ok) setCompanies((items) => items.map((item) => item.slug === company.slug ? { ...item, status } : item)); }
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">مدیریت پلتفرم</h1>{error ? <p className="mt-4" role="alert">{error}</p> : <div className="mt-6 overflow-x-auto rounded border"><table className="w-full text-right"><thead><tr className="border-b"><th className="p-3">شرکت</th><th>شناسه</th><th>وضعیت</th><th></th></tr></thead><tbody>{companies.map((company) => <tr className="border-b" key={company.slug}><td className="p-3">{company.name}</td><td dir="ltr">{company.slug}</td><td>{company.status === "active" ? "فعال" : "معلق"}</td><td><button onClick={() => toggle(company)} className="rounded border px-3 py-1">{company.status === "active" ? "تعلیق" : "فعال‌سازی"}</button></td></tr>)}</tbody></table></div>}</main>;
}
