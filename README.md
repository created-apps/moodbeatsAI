# 🎵 MoodBeats AI

> **Detect your emotion. Get your soundtrack.**
> A smart, multi-page web app that reads your facial expression or mood description and instantly recommends music — powered by Google Gemini AI.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-4285F4?logo=google&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-CDN-06B6D4?logo=tailwindcss&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46A2F1?logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Table of Contents

- [What is MoodBeats AI?](#what-is-moodbeats-ai)
- [Live Demo](#live-demo)
- [Features](#features)
- [Architecture](#architecture)
  - [System Overview](#system-overview)
  - [Request Flow](#request-flow)
  - [File Structure](#file-structure)
  - [File-by-File Analysis](#file-by-file-analysis)
- [Pages](#pages)
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
  - [Environment Variables](#environment-variables)
- [Supabase Setup (Optional)](#supabase-setup-optional)
- [Deploy on Render](#deploy-on-render)
- [How the AI Works](#how-the-ai-works)
- [Music Link Strategy](#music-link-strategy)
- [Contributing](#contributing)
- [License](#license)

---

## What is MoodBeats AI?

MoodBeats AI is a **Python-only multi-page web application** that:

1. **Detects your emotion** via webcam facial expression analysis **or** a typed mood description
2. **Classifies the mood** using Google Gemini 1.5 Flash (free tier, multimodal LLM)
3. **Recommends 8 songs** perfectly matched to your emotional state
4. **Provides instant links** to Spotify, YouTube Music, and YouTube — no API keys needed

It is intentionally designed to use **zero paid APIs** beyond the Gemini free tier (1,500 requests/day).

---

## Live Demo

> _Deploy your own in under 5 minutes — see [Deploy on Render](#deploy-on-render)._

---

## Features

| Feature | Details |
|---|---|
| 📸 **Face Detection** | Webcam capture via browser `getUserMedia` API → PIL Image → Gemini vision |
| ✍️ **Text Input** | Describe your mood in plain English; Gemini detects the underlying emotion |
| 🎭 **15 Emotions** | happy · sad · angry · fearful · surprised · disgusted · neutral · calm · excited · melancholic · romantic · energetic · anxious · peaceful · nostalgic |
| 🎵 **8 Songs per Mood** | Genre-diverse recommendations with title, artist, year, genre, and reason |
| 🔗 **Direct Links** | Spotify search, YouTube Music search, and YouTube — all without API keys |
| 📋 **Mood History** | Session-based history stored in Supabase (gracefully optional) |
| 👤 **Profile Page** | Stats, display name, recent detections, input breakdown |
| 🆓 **Fully Free Stack** | Gemini free tier + Supabase free tier + Render free tier |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (User)                      │
│  Landing → Detect → Results → History → Profile         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   Render (Free Tier)                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │            FastAPI (app.py + Uvicorn)           │   │
│  │                                                 │   │
│  │  ┌────────────┐   ┌─────────────────────────┐  │   │
│  │  │ routers/   │   │      services/          │  │   │
│  │  │ pages.py   │   │  gemini_service.py      │  │   │
│  │  │ (GET only) │   │  music_service.py       │  │   │
│  │  │            │   │  supabase_service.py    │  │   │
│  │  │ api.py     │   └────────────┬────────────┘  │   │
│  │  │ (POST only)│                │               │   │
│  │  └────────────┘   ┌────────────▼────────────┐  │   │
│  │                   │        core/            │  │   │
│  │  ┌─────────────┐  │  result_cache.py        │  │   │
│  │  │ templates/  │  │  session.py             │  │   │
│  │  │ Jinja2 HTML │  └─────────────────────────┘  │   │
│  │  └─────────────┘                               │   │
│  └─────────────────────────────────────────────────┘   │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌───────────────────────┐
│  Google Gemini   │      │   Supabase (optional)  │
│  1.5 Flash API   │      │   mood_history table   │
│  (free tier)     │      │   (free tier)          │
└──────────────────┘      └───────────────────────┘
```

### Request Flow

```
[User on /detect]
     │
     │  1. Webcam frame captured as JPEG base64 (JS)
     │     OR mood text typed by user
     │
     ▼
[POST /detect]   ←─── routers/api.py
     │
     │  2. Validate input
     │  3. Call GeminiService.analyze_image() or analyze_text()
     │  4. Gemini returns JSON: {emotion, confidence, mood_description, songs[]}
     │  5. music_service.enrich() adds Spotify/YT URLs to each song
     │  6. result_cache.store(result) → UUID key
     │  7. supabase_service.save_mood(session_id, ...)
     │
     │  HTTP 303 Redirect → /results?key=<uuid>
     ▼
[GET /results?key=uuid]   ←─── routers/pages.py
     │
     │  8. result_cache.retrieve(key) → result dict
     │  9. music_service.get_theme(emotion) → visual theme (hex colors)
     │  10. Render results.html with Jinja2
     │
     ▼
[User sees playlist with Spotify / YouTube links]
```

### File Structure

```
moodbeats-ai/
│
├── app.py                        # FastAPI app factory, middleware, lifespan, error handlers
│
├── core/
│   ├── __init__.py
│   ├── result_cache.py           # In-memory TTL cache: UUID → result dict
│   └── session.py                # Helpers for Starlette session cookie
│
├── routers/
│   ├── __init__.py
│   ├── pages.py                  # All GET routes (render Jinja2 templates)
│   └── api.py                    # All POST routes (process & redirect)
│
├── services/
│   ├── __init__.py
│   ├── gemini_service.py         # GeminiService: analyze_image(), analyze_text()
│   ├── music_service.py          # enrich(), get_theme(), EMOTION_THEMES, link generators
│   └── supabase_service.py       # save_mood(), get_history() — optional
│
├── templates/
│   ├── base.html                 # Shared layout: navbar, loading overlay, footer
│   ├── landing.html              # Hero, feature cards, how-it-works, CTA
│   ├── detect.html               # Webcam tab + text tab, shared form
│   ├── results.html              # Emotion banner, confidence bar, song grid
│   ├── history.html              # Past detections table with stats
│   ├── profile.html              # Session stats, name form, recent detections
│   └── error.html                # 404 / 500 error page
│
├── static/
│   ├── css/
│   │   └── custom.css            # Animations, custom components, scrollbar
│   └── js/
│       ├── app.js                # Shared: mobile nav, loading overlay, toasts, tabs
│       └── webcam.js             # getUserMedia, capture, canvas → base64, form submit
│
├── requirements.txt
├── .env.example                  # Template for environment variables
├── Dockerfile                    # Production container (python:3.11-slim)
├── render.yaml                   # Render deployment config
├── .gitignore
└── README.md
```

### File-by-File Analysis

#### `app.py` — Application Entry Point
- Creates the FastAPI app with `lifespan` context manager
- Initialises `GeminiService` once at startup; stores in `app.state.gemini`
- Adds `SessionMiddleware` (Starlette) for signed cookie sessions
- Mounts `/static` directory and includes both routers
- Registers custom 404 and 500 error handlers

#### `core/result_cache.py` — Result Cache
- Module-level `dict[str, tuple[dict, float]]` — no Redis, no database
- `store(result)` → generates UUID, writes `(result, monotonic_time)`, prunes expired
- `retrieve(key)` → returns result or `None` if expired (TTL = 1 hour)
- Hard cap of 500 entries; evicts oldest 50 on overflow
- **Why not sessions/cookies?** A full 8-song result with reasons can exceed the 4KB cookie limit

#### `core/session.py` — Session Helpers
- Thin wrappers around `request.session` (dict backed by `SessionMiddleware`)
- `get_or_create_id(request)` — creates a UUID session ID on first visit
- `get_display_name / set_display_name` — user preference stored in session cookie

#### `routers/pages.py` — GET Handlers
- All routes are read-only; they query the cache/DB and render templates
- Never imports from `routers/api.py` — circular imports avoided via `core/`
- Computes session stats (emotion counter, face/text breakdown) for the profile page

#### `routers/api.py` — POST Handlers
- `POST /detect` — unified handler for both face and text modes
  - Reads `input_type` hidden field to branch logic
  - Decodes base64 image → PIL Image → Gemini
  - On success: enriches songs, caches result, saves to Supabase, redirects 303
  - On error: redirects to `/detect?error=<message>` (no error pages mid-form)
- `POST /profile/update` — saves display name to session

#### `services/gemini_service.py` — Gemini Integration
- Initialised once via `app.state.gemini` (lifespan)
- `analyze_image(PIL.Image)` — sends image + structured prompt to Gemini vision
- `analyze_text(str)` — sends text + structured prompt
- Both return a `dict` with `{emotion, confidence, mood_description, songs[]}`
- `_parse()` strips markdown fences, extracts JSON, sets safe defaults

#### `services/music_service.py` — Music Data
- `enrich(result)` — adds `spotify_url`, `yt_music_url`, `youtube_url` to every song
- `get_theme(emotion)` — returns `{accent, bg, border, emoji}` hex dict
- `EMOTION_THEMES` — 15 emotion → visual theme mappings (used in templates via `get_theme`)
- Link generators use `urllib.parse.quote` — no external API calls

#### `services/supabase_service.py` — Database (Optional)
- `save_mood(session_id, input_type, result)` — inserts to `mood_history` table
- `get_history(session_id, limit)` — fetches rows ordered by `created_at DESC`
- Gracefully returns `[]` / `False` if Supabase is not configured

#### `templates/base.html` — Shared Layout
- Tailwind CSS Play CDN (no build step)
- Inter font from Google Fonts
- Fixed navbar with active link highlighting via `active_page` context variable
- Full-screen loading overlay (`#loading-overlay`) shared across all pages
- Mobile hamburger menu

#### `static/js/webcam.js` — Camera Logic
- `startWebcam()` → `getUserMedia({ video: true })` → sets `<video>.srcObject`
- `captureFrame()` → draws frame to `<canvas>` → `toDataURL('image/jpeg', 0.85)` → sets hidden input
- Toggle between live feed and captured preview (retake flow)
- `submitFaceForm()` → validates image present → `showLoading()` → submits form
- Stops camera tracks on `beforeunload`

---

## Pages

| Route | Page | Description |
|---|---|---|
| `GET /` | **Landing** | Hero, feature cards, how-it-works, emotion strip, CTA |
| `GET /detect` | **Detect** | Webcam tab + text tab; shared form POSTing to `/detect` |
| `POST /detect` | _(redirect)_ | Processes input, redirects to `/results?key=uuid` |
| `GET /results` | **Results** | Emotion banner, confidence bar, 8 song cards with links |
| `GET /history` | **History** | All past detections for the session with stats summary |
| `GET /profile` | **Profile** | Session info, display name form, stats, recent detections |
| `POST /profile/update` | _(redirect)_ | Saves display name to session cookie |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | Fast, async, modern Python; excellent Render support |
| **Templates** | Jinja2 | Server-side rendering; no JS framework needed |
| **Styling** | Tailwind CSS (CDN) | Zero build step; works without Node.js |
| **LLM** | Google Gemini 1.5 Flash | Free tier (1,500 req/day), multimodal (image + text) |
| **Music Links** | Spotify & YouTube URLs | No API keys; `open.spotify.com/search/query` pattern |
| **Sessions** | Starlette `SessionMiddleware` | Signed cookies; no Redis needed |
| **Cache** | In-memory Python dict | No external deps; sufficient for single-process deployment |
| **Database** | Supabase | Free tier; Python SDK; mood history persistence |
| **Deployment** | Render | Native Python support; free tier; auto-HTTPS |

---

## Local Development

### Prerequisites

- Python 3.11 or later
- A **Gemini API key** (free) — get one at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- _(Optional)_ Supabase account for mood history

### Setup Steps

```bash
# 1. Clone / download the project
git clone <your-repo-url>
cd moodbeats-ai

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and set GEMINI_API_KEY (and optionally SECRET_KEY, SUPABASE_*)

# 5. Run the development server
python app.py
# or with auto-reload:
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

> **Webcam note:** Modern browsers require a **secure context** (HTTPS or `localhost`) for camera access. Local development on `http://localhost:8000` works fine.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key. Free tier: 1,500 requests/day, 15 req/min |
| `SECRET_KEY` | ✅ Yes | Random string for signing session cookies. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SUPABASE_URL` | ❌ Optional | Your Supabase project URL (`https://xxx.supabase.co`) |
| `SUPABASE_KEY` | ❌ Optional | Supabase anon (public) key |
| `PORT` | ❌ Optional | Server port. Default: `8000`. Render sets this automatically. |

---

## Supabase Setup (Optional)

Without Supabase, the app runs fully — the history page simply shows "no data yet".

### 1. Create a free Supabase project at [supabase.com](https://supabase.com)

### 2. Run this SQL in the Supabase SQL Editor

```sql
create table if not exists mood_history (
  id           uuid primary key default gen_random_uuid(),
  session_id   text            not null,
  input_type   text            not null,   -- 'face' | 'text'
  emotion      text            not null,
  confidence   int             not null,
  songs        jsonb           not null default '[]',
  created_at   timestamptz     not null default now()
);

-- Index for fast per-session lookups
create index on mood_history (session_id, created_at desc);

-- Row-level security (allow all for simplicity — tighten in production)
alter table mood_history enable row level security;
create policy "allow_all" on mood_history for all using (true);
```

### 3. Add to your `.env`

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_anon_key_here
```

---

## Deploy on Render

### Method A — `render.yaml` (recommended, 1 click)

1. Push this project to a GitHub/GitLab repository
2. Go to [render.com](https://render.com) → **New → Blueprint**
3. Connect your repository — Render detects `render.yaml` automatically
4. Set the secret environment variables in the Render dashboard:
   - `GEMINI_API_KEY` → your Gemini key
   - `SUPABASE_URL` and `SUPABASE_KEY` → if using history
   - `SECRET_KEY` → auto-generated by `generateValue: true` in `render.yaml`
5. Click **Apply** — deployment takes ~2 minutes

### Method B — Manual Web Service

1. Push to GitHub
2. Render → **New Web Service** → connect repo
3. Set:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add environment variables under **Environment**
5. Deploy

### Method C — Docker

```bash
# Build
docker build -t moodbeats-ai .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  moodbeats-ai
```

> **Render free tier note:** The server sleeps after 15 minutes of inactivity. First request after sleep takes ~10 seconds to cold-start. This is normal on the free plan.

---

## How the AI Works

MoodBeats AI uses **Google Gemini 1.5 Flash** — a multimodal LLM — instead of a traditional trained ML model. This has several advantages:

| Traditional ML Model | Gemini LLM Approach |
|---|---|
| Requires training data | Zero training required |
| Fixed emotion labels | Flexible, context-aware |
| Separate image/text models | Single multimodal model |
| Needs GPU for inference | API call — no hardware needed |
| Maintenance overhead | Continuously updated by Google |

### Prompt Design

The prompt instructs Gemini to:
1. Identify the primary emotion from a fixed list of 15
2. Return a confidence score (0–100)
3. Write a 2–3 sentence empathetic mood description
4. Recommend exactly 8 songs with title, artist, year, genre, and a matching reason
5. Return **only** valid JSON (no markdown, no extra text)

The response parser strips any markdown code fences and uses `json.loads()` with a regex fallback.

### Gemini Free Tier Limits

| Metric | Limit |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | 1,500 RPD |
| Tokens per minute | 1,000,000 TPM |
| Cost | **$0** |

---

## Music Link Strategy

MoodBeats AI generates direct music links **without any music API**:

```python
# Spotify search link (opens Spotify app or web player)
https://open.spotify.com/search/{url_encoded_query}

# YouTube Music search link
https://music.youtube.com/search?q={url_encoded_query}

# YouTube search link
https://www.youtube.com/results?search_query={url_encoded_query}
```

When the user clicks a Spotify link, Spotify's own search finds the track. This requires no API key, no OAuth, and no rate limits.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

```bash
# Development setup
pip install -r requirements.txt
uvicorn app:app --reload
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ♥ using FastAPI & Google Gemini AI*
