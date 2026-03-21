"""
MoodBeats AI — Session Helpers
Thin wrappers around Starlette's SessionMiddleware-backed request.session dict.
"""

import uuid
from starlette.requests import Request


def get_or_create_id(request: Request) -> str:
    """Return existing session_id or create a new one."""
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return request.session["session_id"]


def get_display_name(request: Request) -> str:
    return request.session.get("display_name", "")


def set_display_name(request: Request, name: str) -> None:
    request.session["display_name"] = name.strip()
