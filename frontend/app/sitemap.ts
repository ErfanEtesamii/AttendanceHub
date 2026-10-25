import type { MetadataRoute } from "next";
const pages = ["", "/about", "/contact", "/terms", "/privacy"];
export default function sitemap(): MetadataRoute.Sitemap { const base = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"; return pages.map((path) => ({ url: `${base}${path}`, lastModified: new Date() })); }
