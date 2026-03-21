"""
MoodBeats AI — Gemini Service
Handles all Gemini API interactions for emotion detection and song recommendations.
"""

import io
import json
import logging
import os
import re

from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"

# ── Prompts ──────────────────────────────────────────────────────────────────

_JSON_SCHEMA = """\
Return ONLY valid JSON, no markdown, no extra text:
{
  "emotion": "<one of the listed emotions>",
  "confidence": <integer 0-100>,
  "mood_description": "<warm 2-3 sentence description of the detected mood>",
  "songs": [
    {
      "title": "<song title>",
      "artist": "<artist name>",
      "year": "<release year>",
      "genre": "<genre>",
      "reason": "<why this song matches the mood>"
    }
  ]
}
Provide exactly 8 songs. Mix genres: pop, rock, indie, jazz, hip-hop, classical, r&b, electronic.\
"""

IMAGE_PROMPT = f"""\
You are an expert emotion analyst and music curator.

Carefully study the facial expression in this image. Detect the primary emotion from:
happy, sad, angry, fearful, surprised, disgusted, neutral, calm, excited, melancholic,
romantic, energetic, anxious, peaceful, nostalgic

Then recommend 8 songs that perfectly match the emotional state.
Each recommendation should feel intentional — not generic.

{_JSON_SCHEMA}
"""


def _text_prompt(user_text: str) -> str:
    return f"""\
You are an expert emotion analyst and music curator.

The user describes their current feeling as:
"{user_text}"

Analyse this carefully. Identify the primary emotion from:
happy, sad, angry, fearful, surprised, disgusted, neutral, calm, excited, melancholic,
romantic, energetic, anxious, peaceful, nostalgic

Then recommend 8 songs that perfectly match the emotional state.
Each recommendation should feel intentional — not generic.

{_JSON_SCHEMA}
"""


# ── Service ───────────────────────────────────────────────────────────────────

class GeminiService:
    """Wraps Google Gemini for emotion detection and music curation."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Get a free key at https://aistudio.google.com/app/apikey"
            )
        self._client = genai.Client(api_key=api_key)
        self._config = types.GenerateContentConfig(
            temperature=0.75,
            top_p=0.95,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )
        logger.info("GeminiService initialised with %s", MODEL)

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze_image(self, image: Image.Image) -> dict:
        """Detect emotion from a PIL Image and return structured result."""
        logger.info("Sending image to Gemini for analysis")
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG")
        img_part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")
        response = self._client.models.generate_content(
            model=MODEL,
            contents=[IMAGE_PROMPT, img_part],
            config=self._config,
        )
        return self._parse(response.text)

    def analyze_text(self, text: str) -> dict:
        """Detect emotion from a text description and return structured result."""
        logger.info("Sending text to Gemini for analysis")
        response = self._client.models.generate_content(
            model=MODEL,
            contents=_text_prompt(text),
            config=self._config,
        )
        return self._parse(response.text)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse(raw: str) -> dict:
        """Extract and validate JSON from a Gemini response string."""
        # JSON mode returns clean JSON, but strip fences as a fallback guard
        text = re.sub(r"```(?:json)?", "", raw).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: find the first {...} block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError(f"No JSON found in Gemini response:\n{raw[:500]}")
            data = json.loads(match.group())

        data.setdefault("emotion", "neutral")
        data.setdefault("confidence", 70)
        data.setdefault("mood_description", "")
        data.setdefault("songs", [])
        data["emotion"] = data["emotion"].lower().strip()
        return data
