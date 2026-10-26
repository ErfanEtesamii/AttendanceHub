"use client";

import { useEffect, useState } from "react";

type AuditEntry = { action: string; created_at: string };

export default function AuditPage({ params }: { params: Promise<{ slug: string }> }) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    params
      .then(({ slug }) => fetch(`/api/v1/companies/${slug}/audit`))
      .then(async (response) => {
        if (!response.ok) throw new Error();
        return response.json();
      })
      .then(setEntries)
      .catch(() => setError("اجازهٔ مشاهدهٔ رویدادها را ندارید."));
  }, [params]);
  return <main className="mx-auto max-w-3xl p-8"><h1 className="text-2xl font-bold">رویدادهای امنیتی و مدیریتی</h1>{error ? <p className="mt-4" role="alert">{error}</p> : <ul className="mt-6 space-y-2">{entries.length ? entries.map((entry, index) => <li className="rounded border p-3" key={`${entry.created_at}-${index}`}><span>{entry.action}</span><time className="mr-3 text-sm text-slate-600" dir="ltr">{new Date(entry.created_at).toLocaleString("fa-IR")}</time></li>) : <li className="rounded border p-3">هنوز رویدادی ثبت نشده است.</li>}</ul>}</main>;
}
