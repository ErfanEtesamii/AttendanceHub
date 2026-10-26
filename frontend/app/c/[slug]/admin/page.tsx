import Link from "next/link";

export default async function CompanyAdminPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">پنل مدیریت شرکت</h1><p className="mt-3">شرکت: {slug}</p><nav className="mt-6 flex flex-wrap gap-4"><Link href={`/c/${slug}/admin/members`}>اعضا و دعوت‌ها</Link><Link href={`/c/${slug}/admin/attendance-policy`}>سیاست حضور</Link><Link href={`/c/${slug}/admin/bot`}>اتصال بات</Link></nav></main>;
}
