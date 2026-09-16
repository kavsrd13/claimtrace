"""
ClaimTrace – FastAPI application entrypoint.
"""

import logging
import sys
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

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(sessions.router)
app.include_router(documents.router)
app.include_router(compare.router)
app.include_router(qa.router)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


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
