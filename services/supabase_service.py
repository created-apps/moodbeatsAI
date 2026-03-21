"""
MoodBeats AI — Supabase Service  (optional)
Stores mood history per session. Safe to skip — app runs fine without Supabase keys.

Required Supabase table (run in SQL editor):
-----------------------------------------------
create table if not exists mood_history (
  id           uuid primary key default gen_random_uuid(),
  session_id   text,
  input_type   text,          -- 'face' | 'text'
  emotion      text,
  confidence   int,
  songs        jsonb,
  created_at   timestamptz default now()
);
alter table mood_history enable row level security;
create policy "allow_all" on mood_history for all using (true);
-----------------------------------------------
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_client():
    """Lazily build the Supabase client so missing keys don't crash the app."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as exc:
        logger.warning("Supabase client error: %s", exc)
        return None


def save_mood(
    session_id: str,
    input_type: str,
    result: dict,
) -> bool:
    """
    Persist a mood-detection result.
    Returns True on success, False when Supabase is not configured or fails.
    """
    client = _get_client()
    if client is None:
        return False

    try:
        client.table("mood_history").insert({
            "session_id": session_id,
            "input_type": input_type,
            "emotion":    result.get("emotion", "unknown"),
            "confidence": result.get("confidence", 0),
            "songs":      result.get("songs", []),
        }).execute()
        logger.info("Saved mood history for session %s", session_id)
        return True
    except Exception as exc:
        logger.warning("Failed to save mood history: %s", exc)
        return False


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    """Fetch the last `limit` mood records for a session."""
    client = _get_client()
    if client is None:
        return []

    try:
        resp = (
            client.table("mood_history")
            .select("emotion, confidence, input_type, songs, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        logger.warning("Failed to fetch history: %s", exc)
        return []
