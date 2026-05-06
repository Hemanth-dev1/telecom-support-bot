"""
In-memory rate limiter using a sliding window counter per IP.

30 requests/minute per IP on /chat.
/webhook is excluded (Dialogflow calls it, not end users).

For multi-instance Cloud Run deployments, replace the in-memory
store with Redis (via google-cloud-redis) so limits are shared
across instances. For a single-instance deployment this is fine.
"""
import time
import asyncio
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status
from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

_log = logging.getLogger("app")

# ── Store: ip → list of request timestamps ────────────────────────
_store: dict[str, list[float]] = defaultdict(list)
_lock = asyncio.Lock()


def _get_ip(request: Request) -> str:
    """
    Extract real client IP.
    Cloud Run sits behind Google's load balancer which sets
    X-Forwarded-For. We take the first (leftmost) address
    which is the original client, not the proxy.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_chat(request: Request) -> None:
    """
    FastAPI dependency — raises 429 if the IP exceeds RATE_LIMIT_REQUESTS
    within the last RATE_LIMIT_WINDOW seconds.
    """
    ip  = _get_ip(request)
    now = time.time()

    async with _lock:
        timestamps = _store[ip]

        # Drop timestamps outside the current window
        cutoff = now - RATE_LIMIT_WINDOW
        _store[ip] = [t for t in timestamps if t > cutoff]

        count = len(_store[ip])

        if count >= RATE_LIMIT_REQUESTS:
            _log.warning(
                "rate_limit_exceeded",
                extra={"ip": ip, "count": count, "window": RATE_LIMIT_WINDOW},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many requests. "
                    f"Limit is {RATE_LIMIT_REQUESTS} per {RATE_LIMIT_WINDOW}s. "
                    f"Please wait before trying again."
                ),
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )

        _store[ip].append(now)
        _log.debug(
            "rate_limit_ok",
            extra={"ip": ip, "count": count + 1, "limit": RATE_LIMIT_REQUESTS},
        )
