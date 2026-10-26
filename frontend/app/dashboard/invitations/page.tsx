"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export default function InvitationsPage() {
  const params = useSearchParams(); const router = useRouter(); const [message, setMessage] = useState("");
  async function accept() { const token = params.get("token"); if (!token) return setMessage("لینک دعوت معتبر نیست."); const response = await fetch(`/api/v1/companies/invitations/accept?token=${encodeURIComponent(token)}`, { method: "POST" }); const body = await response.json(); if (response.ok) router.replace(`/c/${body.slug}/admin`); else setMessage("دعوت‌نامه معتبر نیست، منقضی شده یا با ایمیل حساب شما سازگار نیست."); }
  return <main className="mx-auto max-w-lg p-8"><h1 className="text-2xl font-bold">دعوت به شرکت</h1><p className="mt-3">پس از پذیرش، نقش تعیین‌شده برای شما در شرکت فعال می‌شود.</p><button onClick={accept} className="mt-6 rounded bg-[var(--primary)] px-4 py-2 text-white">پذیرش دعوت</button>{message && <p className="mt-4" role="alert">{message}</p>}</main>;
}
