from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.routers.auth import router as auth_router
from app.routers.companies import router as companies_router
from app.routers.platform import router as platform_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None, redoc_url=None)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"} and (request.cookies.get("ah_access") or request.cookies.get("ah_refresh")):
            origin = request.headers.get("origin")
            if not origin or origin not in settings.cors_origin_list:
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
    return {"status": "ok", "service": settings.app_name}
