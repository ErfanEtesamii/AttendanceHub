from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.auth import router as auth_router
from app.routers.companies import router as companies_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(auth_router)
app.include_router(companies_router)


@app.get("/api/v1/health", tags=["operations"])
def health() -> dict[str, str]:
    """Liveness endpoint intentionally excludes configuration secrets."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
