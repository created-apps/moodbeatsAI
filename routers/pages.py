"""
MoodBeats AI — Pages Router  (GET handlers only)
Each route renders a Jinja2 template.
"""

import collections
import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core import result_cache, session as sess
from services import supabase_service as db
from services.music_service import EMOTION_THEMES, get_theme

logger = logging.getLogger(__name__)
router  = APIRouter()
tmpl    = Jinja2Templates(directory="templates")

_TEXT_EXAMPLES = [
    "I'm feeling super happy and want to dance all night!",
    "I'm sad and missing someone I love deeply.",
    "Feeling really stressed and anxious about a big deadline.",
    "Just calm and peaceful, sipping tea and watching rain.",
    "Nostalgic — old songs keep playing in my head.",
    "Excited and pumped up, can't wait for tonight!",
    "Angry and frustrated, nothing is going my way today.",
    "Feeling romantic and completely in love 💕",
]


# ── Landing ───────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return tmpl.TemplateResponse("landing.html", {
        "request":     request,
        "active_page": "home",
        "themes":      EMOTION_THEMES,
    })


# ── Detect ────────────────────────────────────────────────────────────────────

@router.get("/detect", response_class=HTMLResponse)
async def detect(request: Request, error: str = ""):
    return tmpl.TemplateResponse("detect.html", {
        "request":      request,
        "active_page":  "detect",
        "error":        error,
        "text_examples": _TEXT_EXAMPLES,
    })


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/results", response_class=HTMLResponse)
async def results(request: Request, key: str = ""):
    result = result_cache.retrieve(key) if key else None
    theme  = get_theme(result["emotion"]) if result else None
    return tmpl.TemplateResponse("results.html", {
        "request":     request,
        "active_page": "detect",
        "result":      result,
        "theme":       theme,
        "key":         key,
    })


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    session_id = sess.get_or_create_id(request)
    rows       = db.get_history(session_id)

    # Add theme data to each row for template colouring
    for row in rows:
        row["theme"] = get_theme(row.get("emotion", "neutral"))

    return tmpl.TemplateResponse("history.html", {
        "request":     request,
        "active_page": "history",
        "rows":        rows,
    })


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    session_id   = sess.get_or_create_id(request)
    display_name = sess.get_display_name(request)
    rows         = db.get_history(session_id, limit=100)

    emotions    = [r.get("emotion", "") for r in rows]
    input_types = [r.get("input_type", "") for r in rows]
    total       = len(rows)
    top_emotion = collections.Counter(emotions).most_common(1)[0][0] if emotions else None
    face_count  = input_types.count("face")
    text_count  = input_types.count("text")
    recent      = rows[:5]

    for row in recent:
        row["theme"] = get_theme(row.get("emotion", "neutral"))

    return tmpl.TemplateResponse("profile.html", {
        "request":      request,
        "active_page":  "profile",
        "session_id":   session_id[:8] + "…" if session_id else "N/A",
        "display_name": display_name,
        "total":        total,
        "top_emotion":  top_emotion,
        "top_theme":    get_theme(top_emotion) if top_emotion else None,
        "face_count":   face_count,
        "text_count":   text_count,
        "recent":       recent,
    })
