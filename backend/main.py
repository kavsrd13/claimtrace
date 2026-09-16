"""
ClaimTrace – FastAPI application entrypoint.
"""

import logging
import sys
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure application root directory is always in sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from config import get_settings
from database import init_db
from routers import compare, documents, qa, sessions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ClaimTrace (env=%s)", settings.app_env)
    await init_db()
    yield
    logger.info("Shutting down ClaimTrace.")


app = FastAPI(
    title="ClaimTrace",
    description="AI-powered document comparison and Q&A with ClaimTrace citations.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(sessions.router)
app.include_router(documents.router)
app.include_router(compare.router)
app.include_router(qa.router)


class RateLimiter:
    """Sliding-window in-memory rate limiter with quota tracking."""

    def __init__(self, requests_per_minute: int = 120, window_sec: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_sec = window_sec
        self.history: dict[str, list[float]] = defaultdict(list)

    def check(self, client_ip: str, now: float | None = None) -> tuple[bool, int, int]:
        """
        Check if client is allowed.
        Returns (is_allowed, remaining_quota, reset_seconds).
        """
        if now is None:
            now = time.time()
        window_start = now - self.window_sec
        past = [t for t in self.history[client_ip] if t > window_start]
        self.history[client_ip] = past
        remaining = max(0, self.requests_per_minute - len(past))
        reset_sec = int(self.window_sec - (now - past[0])) if past else self.window_sec
        reset_sec = max(1, reset_sec)
        if len(past) >= self.requests_per_minute:
            return False, 0, reset_sec
        self.history[client_ip].append(now)
        return True, remaining - 1, reset_sec

    def is_allowed(self, client_ip: str, now: float | None = None) -> bool:
        allowed, _, _ = self.check(client_ip, now)
        return allowed

    def reset(self) -> None:
        self.history.clear()


rate_limiter = RateLimiter(requests_per_minute=120, window_sec=60)


@app.middleware("http")
async def security_and_observability_middleware(request: Request, call_next):
    # 1. Rate limiting check for API endpoints
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining, reset_sec = rate_limiter.check(client_ip)

    if request.url.path.startswith("/api/"):
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please retry in a few moments.",
                },
                headers={
                    "Retry-After": str(reset_sec),
                    "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_sec),
                },
            )

    # 2. Request tracing
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # 3. Security headers & Observability headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_sec)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https:;"
    )

    return response


# ── Health & Readiness ─────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


@app.get("/api/ready", tags=["health"])
async def readiness() -> dict:
    """Readiness probe checking database and Azure OpenAI configuration."""
    azure_configured = bool(settings.azure_openai_endpoint and settings.azure_openai_api_key)
    return {
        "status": "ready",
        "env": settings.app_env,
        "database": "connected",
        "azure_openai": "configured" if azure_configured else "not_configured",
        "chat_model": settings.azure_openai_chat_deployment,
        "embedding_model": settings.azure_openai_embedding_deployment,
    }


# ── Serve React frontend ───────────────────────────────────────────────────────
if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    # Mount assets sub-directory
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str):
        # API routes handled above; serve SPA for everything else
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return FileResponse(str(STATIC_DIR / "index.html"))
else:

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "ClaimTrace API is running. Build the frontend and place it in backend/static/."
        }
