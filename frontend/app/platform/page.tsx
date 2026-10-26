"use client";

import { useEffect, useState } from "react";

type Company = { name: string; slug: string; timezone: string };

export default function PlatformPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { fetch("/api/v1/platform/companies").then(async (response) => { if (!response.ok) throw new Error(); return response.json(); }).then(setCompanies).catch(() => setError("دسترسی مدیر پلتفرم لازم است.")); }, []);
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">مدیریت پلتفرم</h1>{error ? <p className="mt-4" role="alert">{error}</p> : <div className="mt-6 overflow-x-auto rounded border"><table className="w-full text-right"><thead><tr className="border-b"><th className="p-3">شرکت</th><th>شناسه</th><th>منطقهٔ زمانی</th></tr></thead><tbody>{companies.map((company) => <tr className="border-b" key={company.slug}><td className="p-3">{company.name}</td><td dir="ltr">{company.slug}</td><td dir="ltr">{company.timezone}</td></tr>)}</tbody></table></div>}</main>;
}
