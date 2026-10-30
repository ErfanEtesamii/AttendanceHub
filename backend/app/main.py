from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.client_ip import resolve_client_ip
from app.routers.auth import router as auth_router
from app.routers.companies import router as companies_router
from app.routers.platform import router as platform_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None, redoc_url=None)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if request.url.path.startswith("/api/") and content_length and content_length.isdigit() and int(content_length) > 1_048_576:
            return Response(status_code=413, content="Request body too large")
        if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"} and (request.cookies.get("ah_access") or request.cookies.get("ah_refresh") or request.cookies.get("ah_login_challenge")):
            origin = request.headers.get("origin")
            same_origin_fetch = request.headers.get("sec-fetch-site") == "same-origin"
            if (origin and origin not in settings.cors_origin_list) or (not origin and not same_origin_fetch):
                return Response(status_code=403, content="Cross-site request rejected")
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if settings.environment == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=15552000")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(platform_router)


@app.get("/api/v1/health", tags=["operations"])
def health() -> dict[str, str]:
    """Liveness endpoint intentionally excludes configuration secrets."""
    return {"status": "ok"}


@app.get("/api/v1/network/my-ip", tags=["operations"])
def my_ip(request: Request) -> dict[str, str]:
    address = resolve_client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
        settings.trusted_proxy_networks,
    )
    if address is None:
        raise HTTPException(status_code=400, detail="Unable to determine client IP")
    return {"ip": address}
