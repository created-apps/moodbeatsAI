"""
MoodBeats AI — Music Service
Generates Spotify / YouTube search links and enriches Gemini result dicts.
HTML rendering is now handled by Jinja2 templates; this module is pure data + URLs.
"""

import urllib.parse

# ── Emotion visual themes (hex colours, safe for inline CSS in templates) ─────

EMOTION_THEMES: dict[str, dict] = {
    "happy":       {"accent": "#22c55e", "bg": "#052e16", "border": "#166534", "emoji": "😊"},
    "sad":         {"accent": "#60a5fa", "bg": "#172554", "border": "#1e3a8a", "emoji": "😢"},
    "angry":       {"accent": "#f87171", "bg": "#450a0a", "border": "#7f1d1d", "emoji": "😠"},
    "fearful":     {"accent": "#c084fc", "bg": "#2e1065", "border": "#6b21a8", "emoji": "😨"},
    "surprised":   {"accent": "#fb923c", "bg": "#431407", "border": "#9a3412", "emoji": "😮"},
    "disgusted":   {"accent": "#86efac", "bg": "#052e16", "border": "#15803d", "emoji": "🤢"},
    "neutral":     {"accent": "#94a3b8", "bg": "#1e293b", "border": "#334155", "emoji": "😐"},
    "calm":        {"accent": "#38bdf8", "bg": "#082f49", "border": "#0369a1", "emoji": "😌"},
    "excited":     {"accent": "#fb923c", "bg": "#431407", "border": "#c2410c", "emoji": "🤩"},
    "melancholic": {"accent": "#818cf8", "bg": "#1e1b4b", "border": "#4338ca", "emoji": "😔"},
    "romantic":    {"accent": "#fb7185", "bg": "#4c0519", "border": "#be123c", "emoji": "🥰"},
    "energetic":   {"accent": "#facc15", "bg": "#422006", "border": "#b45309", "emoji": "⚡"},
    "anxious":     {"accent": "#fde047", "bg": "#1c1917", "border": "#713f12", "emoji": "😰"},
    "peaceful":    {"accent": "#34d399", "bg": "#022c22", "border": "#065f46", "emoji": "☮️"},
    "nostalgic":   {"accent": "#d97706", "bg": "#1c1209", "border": "#92400e", "emoji": "🌅"},
}

_DEFAULT_THEME = {"accent": "#a78bfa", "bg": "#1e1b4b", "border": "#4c1d95", "emoji": "🎵"}


def get_theme(emotion: str) -> dict:
    """Return the visual theme dict for a given emotion string."""
    return EMOTION_THEMES.get((emotion or "").lower(), _DEFAULT_THEME)


# ── Link generators ────────────────────────────────────────────────────────────

def _q(text: str) -> str:
    return urllib.parse.quote(text, safe="")


def spotify_link(title: str, artist: str) -> str:
    return f"https://open.spotify.com/search/{_q(f'{title} {artist}')}"


def yt_music_link(title: str, artist: str) -> str:
    return f"https://music.youtube.com/search?q={_q(f'{title} {artist}')}"


def youtube_link(title: str, artist: str) -> str:
    return f"https://www.youtube.com/results?search_query={_q(f'{title} {artist} official')}"


# ── Result enrichment ─────────────────────────────────────────────────────────

def enrich(result: dict) -> dict:
    """
    Add `spotify_url`, `yt_music_url`, `youtube_url` to every song in `result`.
    Mutates and returns the same dict (songs list items are dicts).
    """
    for song in result.get("songs", []):
        t, a = song.get("title", ""), song.get("artist", "")
        song["spotify_url"]  = spotify_link(t, a)
        song["yt_music_url"] = yt_music_link(t, a)
        song["youtube_url"]  = youtube_link(t, a)
    return result
