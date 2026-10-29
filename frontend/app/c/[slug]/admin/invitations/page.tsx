"use client";

import { useEffect, useState } from "react";

type Invitation = { id: string; email: string; role: string; expires_at: string; accepted_at: string | null };

export default function InvitationsPage({ params }: { params: Promise<{ slug: string }> }) {
  const [items, setItems] = useState<Invitation[]>([]); const [message, setMessage] = useState("");
  useEffect(() => { params.then(({ slug }) => fetch(`/api/v1/companies/${slug}/invitations`).then((response) => response.ok ? response.json() : []).then(setItems)); }, [params]);
  async function revoke(id: string) { const slug = (await params).slug; const response = await fetch(`/api/v1/companies/${slug}/invitations/${id}`, { method: "DELETE" }); if (response.ok) setItems((values) => values.filter((item) => item.id !== id)); else setMessage("ابطال دعوت‌نامه ناموفق بود."); }
  return <main className="mx-auto max-w-3xl p-8"><h1 className="text-2xl font-bold">دعوت‌نامه‌ها</h1><ul className="mt-6 space-y-3">{items.length ? items.map((item) => <li key={item.id} className="flex items-center justify-between rounded border p-3"><span dir="ltr">{item.email}</span><span>{item.role}</span>{item.accepted_at ? <span>پذیرفته شد</span> : <button onClick={() => revoke(item.id)} className="rounded border border-red-600 px-3 py-1 text-red-700">ابطال</button>}</li>) : <li className="rounded border p-3">دعوت‌نامه‌ای وجود ندارد.</li>}</ul>{message && <p className="mt-4" role="alert">{message}</p>}</main>;
}
