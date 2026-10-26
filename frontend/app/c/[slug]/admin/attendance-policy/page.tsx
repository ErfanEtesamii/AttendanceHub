"use client";

import { FormEvent, useEffect, useState } from "react";

type Policy = { mode: "ip" | "location"; allowed_cidr: string | null; latitude: string | null; longitude: string | null; radius_meters: number | null };

export default function PolicyPage({ params }: { params: Promise<{ slug: string }> }) {
  const [policy, setPolicy] = useState<Policy | null>(null); const [message, setMessage] = useState("");
  useEffect(() => { params.then(({ slug }) => fetch(`/api/v1/companies/${slug}/attendance-policy`).then((response) => response.ok ? response.json() : null).then(setPolicy)); }, [params]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const slug = (await params).slug; const form = new FormData(event.currentTarget); const mode = String(form.get("mode"));
    const body = mode === "ip" ? { mode, allowed_cidr: form.get("allowed_cidr") } : { mode, latitude: Number(form.get("latitude")), longitude: Number(form.get("longitude")), radius_meters: Number(form.get("radius_meters")) };
    const response = await fetch(`/api/v1/companies/${slug}/attendance-policy`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setMessage(response.ok ? "سیاست حضور ذخیره شد." : "اطلاعات سیاست معتبر نیست یا اجازهٔ تغییر ندارید.");
  }
  if (!policy) return <main className="p-8" aria-busy="true">در حال دریافت سیاست حضور…</main>;
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">سیاست حضور</h1><form onSubmit={save} className="mt-6 space-y-4 rounded border p-5"><label className="block">روش کنترل<select name="mode" defaultValue={policy.mode} className="mt-2 block w-full rounded border p-2"><option value="ip">IP سازمان</option><option value="location">موقعیت جغرافیایی</option></select></label><label className="block">CIDR مجاز برای روش IP<input name="allowed_cidr" dir="ltr" defaultValue={policy.allowed_cidr ?? ""} className="mt-2 w-full rounded border p-2" placeholder="192.168.10.0/24" /></label><div className="grid gap-3 sm:grid-cols-3"><label>عرض جغرافیایی<input name="latitude" dir="ltr" type="number" step="any" defaultValue={policy.latitude ?? ""} className="mt-2 w-full rounded border p-2" /></label><label>طول جغرافیایی<input name="longitude" dir="ltr" type="number" step="any" defaultValue={policy.longitude ?? ""} className="mt-2 w-full rounded border p-2" /></label><label>شعاع (متر)<input name="radius_meters" dir="ltr" type="number" min="10" defaultValue={policy.radius_meters ?? ""} className="mt-2 w-full rounded border p-2" /></label></div><button className="rounded bg-[var(--primary)] px-4 py-2 text-white">ذخیرهٔ سیاست</button></form>{message && <p className="mt-4" aria-live="polite">{message}</p>}</main>;
}
