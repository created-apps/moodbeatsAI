"""
MoodBeats AI — FastAPI Application Entry Point
Run locally:  python app.py
Run via uvicorn:  uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from routers import pages as pages_router
from routers import api   as api_router

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: initialise shared services ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from services.gemini_service import GeminiService
    try:
        app.state.gemini = GeminiService()
        logger.info("Gemini service ready ✓")
    except ValueError as exc:
        app.state.gemini = None
        logger.warning("Gemini service NOT ready: %s", exc)
    yield
    # Shutdown (nothing to clean up)
    logger.info("MoodBeats AI shutting down")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="MoodBeats AI",
    description="Emotion-based music recommendations powered by Gemini AI",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "moodbeats-default-secret-change-in-prod"),
    max_age=86_400 * 30,   # 30 days
    https_only=False,      # Set True in production with HTTPS
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages_router.router)
app.include_router(api_router.router)


# ── Custom error pages ────────────────────────────────────────────────────────

_tmpl = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    logger.debug("404 at %s: %s", request.url, exc)
    return _tmpl.TemplateResponse(
        "error.html",
        {"request": request, "code": 404, "message": "Page not found."},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error(request: Request, exc: Exception):
    logger.error("500 at %s: %s", request.url, exc)
    return _tmpl.TemplateResponse(
        "error.html",
        {"request": request, "code": 500, "message": "Something went wrong on our end."},
        status_code=500,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
