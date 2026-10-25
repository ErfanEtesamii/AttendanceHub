import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: { default: "AttendHub | حضور و غیاب سازمانی", template: "%s | AttendHub" }, description: "درگاه امن راه‌اندازی حضور و غیاب چندشرکتی", robots: { index: true, follow: true } };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fa" dir="rtl"><body>{children}</body></html>;
}
