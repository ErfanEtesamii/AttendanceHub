import { brand } from "@/config/brand";
import fa from "@/messages/fa.json";

export default function Home() {
  return <main className="mx-auto flex min-h-screen max-w-3xl items-center p-8"><section><p className="text-sm font-semibold text-[var(--primary)]">{brand.name}</p><h1 className="mt-3 text-4xl font-bold">{fa.landing.title}</h1><p className="mt-4 text-lg">{fa.landing.description}</p></section></main>;
}
