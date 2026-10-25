"use client";
export default function ErrorPage({ reset }: { reset: () => void }) { return <main className="mx-auto max-w-xl p-10"><h1 className="text-2xl font-bold">مشکلی پیش آمد</h1><p className="mt-3">لطفاً دوباره تلاش کنید.</p><button className="mt-5 rounded bg-[var(--primary)] px-4 py-2 text-white" onClick={reset}>تلاش دوباره</button></main>; }
