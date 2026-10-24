import Link from "next/link";
import { AuthForm } from "@/components/auth/auth-form";
export default function ForgotPasswordPage() { return <main className="mx-auto flex min-h-screen max-w-md items-center p-6"><div className="w-full"><AuthForm mode="forgot" /><Link className="mt-4 block text-[var(--primary)]" href="/verify">کد را دریافت کرده‌ام</Link></div></main>; }
