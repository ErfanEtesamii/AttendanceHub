import { NextRequest, NextResponse } from "next/server";

const protectedPrefixes = ["/dashboard", "/c/", "/platform"];

export function proxy(request: NextRequest) {
  const isProtected = protectedPrefixes.some((prefix) => request.nextUrl.pathname.startsWith(prefix));
  const hasSession = Boolean(request.cookies.get("ah_access")?.value);
  if (isProtected && !hasSession) {
    const url = new URL("/login", request.url);
    url.searchParams.set("callbackUrl", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  if (["/login", "/register"].includes(request.nextUrl.pathname) && hasSession) return NextResponse.redirect(new URL("/dashboard", request.url));
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*", "/c/:path*", "/platform/:path*", "/login", "/register"] };
