"use client";

import { FormEvent, useEffect, useState } from "react";

export default function ProfilePage() {
  const [name, setName] = useState(""); const [message, setMessage] = useState("");
  useEffect(() => { fetch("/api/v1/auth/me").then((response) => response.ok ? response.json() : null).then((data) => { if (data) setName(data.name); }); }, []);
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const response = await fetch("/api/v1/auth/me", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }); setMessage(response.ok ? "پروفایل ذخیره شد." : "ذخیرهٔ پروفایل ناموفق بود."); }
  return <main className="mx-auto max-w-xl p-8"><h1 className="text-2xl font-bold">پروفایل</h1><form onSubmit={save} className="mt-6 rounded border p-5"><label className="block">نام<input value={name} onChange={(event) => setName(event.target.value)} required className="mt-2 w-full rounded border p-2" /></label><button className="mt-4 rounded bg-[var(--primary)] px-4 py-2 text-white">ذخیره</button></form>{message && <p className="mt-4" aria-live="polite">{message}</p>}</main>;
}
