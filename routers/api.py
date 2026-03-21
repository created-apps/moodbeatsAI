"""
MoodBeats AI — API Router  (POST handlers only)
All routes write data and redirect or return JSON.
"""

import base64
import io
import logging

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image

from core import result_cache, session as sess
from services import supabase_service as db
from services.music_service import enrich

logger = logging.getLogger(__name__)
router = APIRouter()


def _gemini(request: Request):
    """Retrieve the shared GeminiService from app state."""
    svc = request.app.state.gemini
    if svc is None:
        raise RuntimeError("Gemini service not initialised — check GEMINI_API_KEY.")
    return svc


# ── Main detection endpoint ───────────────────────────────────────────────────

@router.post("/detect")
async def detect(
    request: Request,
    input_type: str = Form("text"),
    image_data: str = Form(""),
    mood_text:  str = Form(""),
    image_file: UploadFile = File(None),
):
    """
    Unified POST handler for face, upload, and text mood detection.
    On success  → redirect 303 to /results?key=<uuid>
    On error    → redirect 303 to /detect?error=<message>
    """
    session_id = sess.get_or_create_id(request)

    try:
        gemini = _gemini(request)

        if input_type == "face":
            if not image_data:
                return RedirectResponse("/detect?error=No+image+captured", status_code=303)
            _, b64 = image_data.split(",", 1)
            img = Image.open(io.BytesIO(base64.b64decode(b64)))
            result = gemini.analyze_image(img)

        elif input_type == "upload":
            if image_file is None or not image_file.filename:
                return RedirectResponse("/detect?error=No+file+uploaded", status_code=303)
            contents = await image_file.read()
            if not contents:
                return RedirectResponse("/detect?error=Uploaded+file+is+empty", status_code=303)
            img = Image.open(io.BytesIO(contents))
            result = gemini.analyze_image(img)

        else:
            text = mood_text.strip()
            if not text:
                return RedirectResponse("/detect?error=Please+describe+your+mood", status_code=303)
            result = gemini.analyze_text(text)

        enrich(result)
        key = result_cache.store(result)
        db.save_mood(session_id, input_type, result)

        return RedirectResponse(f"/results?key={key}", status_code=303)

    except RuntimeError as exc:
        logger.error("Service error: %s", exc)
        return RedirectResponse(f"/detect?error={str(exc)[:120]}", status_code=303)
    except Exception as exc:
        logger.exception("Detection failed")
        msg = str(exc)[:120].replace(" ", "+")
        return RedirectResponse(f"/detect?error={msg}", status_code=303)


# ── Profile update ────────────────────────────────────────────────────────────

@router.post("/profile/update")
async def update_profile(
    request: Request,
    display_name: str = Form(""),
):
    sess.set_display_name(request, display_name)
    return RedirectResponse("/profile", status_code=303)
