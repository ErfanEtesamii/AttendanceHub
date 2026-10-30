"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function VerifyPage() {
  const [message, setMessage] = useState(""); const [pending, setPending] = useState(false); const params = useSearchParams(); const router = useRouter(); const email = params.get("email") ?? ""; const reset = params.get("reset") === "1"; const twoFactor = params.get("two_factor") === "1";
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setMessage(""); const data = new FormData(event.currentTarget);
    const response = await fetch("/api/v1/auth/otp/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: data.get("email"), code: data.get("code"), ...(reset ? { new_password: data.get("password") } : {}), purpose: reset ? "reset_password" : twoFactor ? "login_2fa" : "verify_email" }) });
    if (response.ok && !reset) router.replace("/dashboard"); else setMessage(response.ok ? "رمز عبور شما تغییر کرد." : "کد نامعتبر یا منقضی است."); setPending(false);
  }
  return <main className="mx-auto flex min-h-screen max-w-md items-center p-6"><form onSubmit={submit} className="w-full rounded-2xl bg-white p-6 shadow-sm"><h1 className="text-2xl font-bold">{reset ? "تأیید و تغییر رمز" : "تأیید ایمیل"}</h1><label className="mt-5 block">ایمیل<input required name="email" type="email" defaultValue={email} className="mt-2 w-full rounded border p-2" /></label><label className="mt-4 block">کد شش‌رقمی<input required name="code" inputMode="numeric" pattern="[0-9]{6}" className="mt-2 w-full rounded border p-2" /></label>{reset && <label className="mt-4 block">رمز جدید<input required name="password" minLength={12} type="password" className="mt-2 w-full rounded border p-2" /></label>}<button disabled={pending} className="mt-6 rounded bg-[var(--primary)] px-4 py-2 text-white disabled:opacity-50">{pending ? "در حال بررسی…" : reset ? "تغییر رمز" : "تأیید و ورود"}</button>{message && <p className="mt-4" aria-live="polite">{message}</p>}</form></main>;
}
