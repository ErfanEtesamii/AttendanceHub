import Link from "next/link";
export default function DashboardPage() { return <main className="p-8"><h1 className="text-2xl font-bold">داشبورد</h1><p className="mt-3">برای شروع، شرکت خود را ثبت کنید.</p><Link className="mt-5 inline-block rounded bg-[var(--primary)] px-4 py-2 text-white" href="/dashboard/companies/new">ثبت شرکت</Link></main>; }
