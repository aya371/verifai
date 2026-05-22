"""
Rate Limiter — Extended with per-user DuckDuckGo search throttling.
Save to: backend/security/rate_limiter.py

Two independent limiters:
1. API rate limiter  — 10 requests/minute per user (existing)
2. Search throttle  — max 5 DuckDuckGo search calls per 60 seconds per user
"""
import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException
from config import config

# ── API Rate Limiter ───────────────────────────────────────────────────────
_api_requests: dict  = defaultdict(list)
_api_lock            = Lock()

def check_rate_limit(user_id: str) -> None:
    """
    Enforce API rate limit: max RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW_MINUTES.
    Raises HTTP 429 if exceeded.
    """
    window = config.RATE_LIMIT_WINDOW_MINUTES * 60
    limit  = config.RATE_LIMIT_REQUESTS
    now    = time.time()

    with _api_lock:
        # Remove timestamps outside the window
        _api_requests[user_id] = [
            t for t in _api_requests[user_id] if now - t < window
        ]
        if len(_api_requests[user_id]) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {limit} requests per "
                       f"{config.RATE_LIMIT_WINDOW_MINUTES} minute(s)."
            )
        _api_requests[user_id].append(now)

# ── Search Throttle ────────────────────────────────────────────────────────
_search_requests: dict = defaultdict(list)
_search_lock           = Lock()
SEARCH_LIMIT           = 5     # max DuckDuckGo calls per window
SEARCH_WINDOW          = 60    # seconds

def check_search_limit(user_id: str) -> None:
    """
    Throttle DuckDuckGo search calls per user.
    Call this once per resolve/CV analysis request (not per individual query).
    Raises HTTP 429 if the user is hammering the search endpoint.
    """
    now = time.time()
    with _search_lock:
        _search_requests[user_id] = [
            t for t in _search_requests[user_id] if now - t < SEARCH_WINDOW
        ]
        if len(_search_requests[user_id]) >= SEARCH_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Search rate limit exceeded. "
                       f"Max {SEARCH_LIMIT} identity analyses per minute."
            )
        _search_requests[user_id].append(now)
