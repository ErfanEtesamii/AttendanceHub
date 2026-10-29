import Link from "next/link";

export default async function AttendancePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <main className="mx-auto max-w-2xl p-8"><h1 className="text-2xl font-bold">حضور و غیاب</h1><section className="mt-6 rounded border p-6"><h2 className="text-lg font-semibold">در حال توسعه</h2><p className="mt-3">موتور اصلی حضور و غیاب از طریق adapter چندشرکتی به این شرکت متصل خواهد شد. تنظیمات سیاست، اعضا و بات در پنل مدیریت آماده‌اند.</p><Link href={`/c/${slug}/admin`} className="mt-5 inline-block text-[var(--primary)] underline">بازگشت به پنل مدیریت</Link></section></main>;
}
