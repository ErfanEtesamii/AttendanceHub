"use client";

import { FormEvent, useState } from "react";

export default function PolicyTestPage({ params }: { params: Promise<{ slug: string }> }) {
  const [result, setResult] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const slug = (await params).slug; const data = new FormData(event.currentTarget); const response = await fetch(`/api/v1/companies/${slug}/attendance-policy/test`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ip: data.get("ip") }) }); const body = await response.json(); setResult(response.ok ? (body.allowed ? "مجاز" : "غیرمجاز") : "خطا در بررسی"); }
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">تست سیاست حضور</h1><form onSubmit={submit} className="mt-6 rounded border p-5"><label>IP آزمایشی<input required name="ip" dir="ltr" placeholder="192.168.10.7" className="mt-2 w-full rounded border p-2" /></label><button className="mt-4 rounded bg-[var(--primary)] px-4 py-2 text-white">بررسی</button></form>{result && <p className="mt-4 font-semibold" aria-live="polite">نتیجه: {result}</p>}</main>;
}
