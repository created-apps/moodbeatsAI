"""
MoodBeats AI — In-Memory Result Cache
Stores Gemini analysis results by UUID key for cross-redirect access.
No external dependencies — works on any single-process deployment (Render free tier).
"""

import uuid
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_TTL_SECONDS = 3600        # Results expire after 1 hour
_MAX_ENTRIES  = 500        # Hard cap; evict oldest when exceeded
_EVICT_COUNT  = 50         # How many to drop on overflow

# key -> (result_dict, stored_timestamp)
_cache: dict[str, tuple[dict, float]] = {}


def store(result: dict) -> str:
    """Store a result dict, return a UUID key."""
    key = str(uuid.uuid4())
    _cache[key] = (result, time.monotonic())
    _prune()
    return key


def retrieve(key: str) -> Optional[dict]:
    """Return the result for `key` if it exists and hasn't expired."""
    entry = _cache.get(key)
    if not entry:
        return None
    result, ts = entry
    if time.monotonic() - ts > _TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return result


def _prune() -> None:
    """Remove expired entries; enforce max size."""
    now = time.monotonic()
    expired = [k for k, (_, ts) in list(_cache.items()) if now - ts > _TTL_SECONDS]
    for k in expired:
        _cache.pop(k, None)

    if len(_cache) > _MAX_ENTRIES:
        # Evict the oldest entries
        sorted_keys = sorted(_cache, key=lambda k: _cache[k][1])
        for k in sorted_keys[:_EVICT_COUNT]:
            _cache.pop(k, None)
        logger.info("Cache overflow: evicted %d entries", _EVICT_COUNT)
