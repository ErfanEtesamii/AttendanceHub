"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

type Mode = "login" | "register" | "forgot";

export function AuthForm({ mode }: { mode: Mode }) {
  const [message, setMessage] = useState(""); const [pending, setPending] = useState(false); const router = useRouter(); const searchParams = useSearchParams();
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setPending(true); setMessage("");
    const data = new FormData(event.currentTarget);
    const url = mode === "forgot" ? "/api/v1/auth/otp/request" : `/api/v1/auth/${mode}`;
    const body = mode === "forgot" ? { email: data.get("email"), purpose: "reset_password" } : mode === "login" ? { identifier: data.get("email"), password: data.get("password") } : { email: data.get("email"), username: data.get("username"), password: data.get("password"), name: data.get("name") };
    try {
      const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin", body: JSON.stringify(body) });
      if (!response.ok) throw new Error();
      const result = mode === "login" ? await response.json() : null;
      if (result?.status === "two_factor_required") {
        router.replace(`/verify?two_factor=1&email=${encodeURIComponent(result.email)}`);
        return;
      }
      if (mode === "forgot") router.replace(`/verify?reset=1&email=${encodeURIComponent(String(data.get("email")))}`);
      else if (mode === "register") router.replace(`/verify?email=${encodeURIComponent(String(data.get("email")))}`);
      else {
        const callbackUrl = searchParams.get("callbackUrl");
        const target = callbackUrl && callbackUrl.startsWith("/") && !callbackUrl.startsWith("//") ? callbackUrl : "/dashboard";
        router.replace(target);
        router.refresh();
      }
    } catch { setMessage("انجام درخواست ممکن نشد. دوباره تلاش کنید."); } finally { setPending(false); }
  };
  return <form onSubmit={submit} className="w-full rounded-2xl bg-white p-6 shadow-sm"><h1 className="text-2xl font-bold">{mode === "login" ? "ورود" : mode === "register" ? "ثبت‌نام" : "بازیابی رمز عبور"}</h1>{mode === "register" && <><label className="mt-6 block">نام<input required name="name" className="mt-2 w-full rounded border p-2" autoComplete="name" /></label><label className="mt-4 block">نام کاربری<input required name="username" pattern="[a-z0-9_]{3,32}" className="mt-2 w-full rounded border p-2" /></label></>}<label className="mt-4 block">ایمیل{mode === "login" ? " یا نام کاربری" : ""}<input required name="email" className="mt-2 w-full rounded border p-2" type={mode === "login" ? "text" : "email"} autoComplete="email" /></label>{mode !== "forgot" && <label className="mt-4 block">رمز عبور<input required name="password" minLength={8} className="mt-2 w-full rounded border p-2" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} /></label>}<button disabled={pending} className="mt-6 rounded bg-[var(--primary)] px-4 py-2 text-white disabled:opacity-50" type="submit">{pending ? "در حال ارسال…" : mode === "forgot" ? "ارسال کد" : mode === "login" ? "ورود" : "ساخت حساب"}</button>{message && <p className="mt-4" aria-live="polite">{message}</p>}</form>;
}
