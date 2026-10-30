import { NextRequest } from "next/server";

const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
const allowedRequestHeaders = ["accept", "accept-language", "content-type", "cookie", "origin", "user-agent"];
const hopByHopHeaders = new Set(["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"]);

async function proxy(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  if (!path.length || path.some((segment) => !segment || segment === "." || segment === ".." || segment.includes("/") || segment.includes("\\"))) return new Response("Invalid path", { status: 400 });
  const headers = new Headers();
  for (const name of allowedRequestHeaders) { const value = request.headers.get(name); if (value) headers.set(name, value); }
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const upstream = new URL(`/api/v1/${path.map(encodeURIComponent).join("/")}`, backendUrl);
    upstream.search = request.nextUrl.search;
    const response = await fetch(upstream, { method: request.method, headers, body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(), redirect: "manual", signal: controller.signal });
    const responseHeaders = new Headers();
    response.headers.forEach((value, name) => { if (!hopByHopHeaders.has(name.toLowerCase()) && name.toLowerCase() !== "set-cookie") responseHeaders.set(name, value); });
    for (const cookie of response.headers.getSetCookie()) responseHeaders.append("set-cookie", cookie);
    return new Response(response.body, { status: response.status, headers: responseHeaders });
  } catch { return new Response("Upstream unavailable", { status: 503 }); } finally { clearTimeout(timeout); }
}
export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE };
