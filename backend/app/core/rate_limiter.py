"""
Token Bucket rate limiter for FastAPI.

Three tiers, configurable via settings/.env:
  - AI endpoints (analysis, worksheet upload): strict — cost-per-call protection
  - Auth endpoints: moderate — brute-force prevention
  - General: default — basic abuse protection

Uses in-memory storage (single-process, suitable for dev/small-scale).
Production multi-worker deployments should swap storage to Redis.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional

from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
from app.core.config import get_settings


# ────────────────────────────────────────────────────────────────────
# Token Bucket
# ────────────────────────────────────────────────────────────────────

@dataclass
class TokenBucket:
    """Leaky-bucket variant: refills at `rate` tokens/sec, capped at `capacity`."""

    rate: float          # tokens per second
    capacity: float      # max burst size
    _tokens: float = field(default=0.0, init=False)
    _last_refill: float = field(default_factory=time.monotonic, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity

    def consume(self, cost: float = 1.0) -> bool:
        """Try to consume `cost` tokens.  Returns True if allowed."""
        now = time.monotonic()
        with self._lock:
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_refill = now
            if self._tokens >= cost:
                self._tokens -= cost
                return True
            return False

    @property
    def available(self) -> float:
        """Current token count (approximate, for debugging)."""
        with self._lock:
            elapsed = time.monotonic() - self._last_refill
            return min(self.capacity, self._tokens + elapsed * self.rate)


# ────────────────────────────────────────────────────────────────────
# Tier definitions
# ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Tier:
    name: str
    rate: float        # tokens / second
    capacity: float     # max burst
    window_human: str   # human-readable description, e.g. "10次/分钟"


# Default tiers — can be overridden via .env settings
def _build_tiers() -> Dict[str, Tier]:
    """Build tier definitions from settings (with fallback defaults)."""
    try:
        s = get_settings()
    except Exception:
        s = None

    ai_rate = (s.RATE_LIMIT_AI_PER_MIN if s else 10) / 60.0
    ai_burst = s.RATE_LIMIT_AI_BURST if s else 10
    auth_rate = (s.RATE_LIMIT_AUTH_PER_MIN if s else 10) / 60.0
    auth_burst = s.RATE_LIMIT_AUTH_BURST if s else 10
    default_rate = (s.RATE_LIMIT_DEFAULT_PER_MIN if s else 120) / 60.0
    default_burst = s.RATE_LIMIT_DEFAULT_BURST if s else 30

    return {
        "ai": Tier(
            name="ai",
            rate=ai_rate,
            capacity=ai_burst,
            window_human=f"{int(ai_rate * 60)}次/分钟",
        ),
        "auth": Tier(
            name="auth",
            rate=auth_rate,
            capacity=auth_burst,
            window_human=f"{int(auth_rate * 60)}次/分钟",
        ),
        "default": Tier(
            name="default",
            rate=default_rate,
            capacity=default_burst,
            window_human=f"{int(default_rate * 60)}次/分钟",
        ),
    }


DEFAULT_TIERS: Dict[str, Tier] = _build_tiers()

# Route prefix → tier mapping
ROUTE_TIER_MAP: Dict[str, str] = {
    "/api/v1/analysis":     "ai",
    "/api/v1/worksheets":   "ai",
    "/api/v1/auth":         "auth",
}


def _get_tier_for_path(path: str) -> Tier:
    """Determine the rate-limit tier for a request path."""
    for prefix, tier_name in ROUTE_TIER_MAP.items():
        if path.startswith(prefix):
            return DEFAULT_TIERS[tier_name]
    return DEFAULT_TIERS["default"]


# ────────────────────────────────────────────────────────────────────
# Rate Limiter middleware
# ────────────────────────────────────────────────────────────────────

class RateLimiter:
    """In-memory rate limiter middleware.

    Usage in create_app():
        rate_limiter = RateLimiter()
        app.middleware("http")(rate_limiter.middleware)
    """

    def __init__(self) -> None:
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        # Periodic cleanup
        self._last_cleanup = time.monotonic()

    def _client_key(self, request: Request) -> str:
        """Build a unique key for the client.

        Uses X-Forwarded-For if behind a proxy, otherwise client host.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the leftmost (original client) IP
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return ip

    def _get_bucket(self, key: str, tier: Tier) -> TokenBucket:
        """Get-or-create a bucket for `key`."""
        # Fast path — most keys already exist
        if key in self._buckets:
            return self._buckets[key]

        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    rate=tier.rate,
                    capacity=tier.capacity,
                )
            return self._buckets[key]

    def _maybe_cleanup(self) -> None:
        """Periodically evict stale buckets to avoid unbounded memory growth."""
        now = time.monotonic()
        if now - self._last_cleanup < 600:  # every 10 minutes
            return
        self._last_cleanup = now
        with self._lock:
            stale = [
                k for k, b in self._buckets.items()
                if b.available >= b.capacity * 0.99  # fully refilled = idle
            ]
            for k in stale:
                del self._buckets[k]

    async def middleware(self, request: Request, call_next):
        """FastAPI/Starlette ASGI middleware entry point."""
        tier = _get_tier_for_path(request.url.path)
        client_key = self._client_key(request)
        bucket_key = f"{tier.name}:{client_key}"

        bucket = self._get_bucket(bucket_key, tier)

        if not bucket.consume():
            retry_after = int(max(1, 1.0 / tier.rate))
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "status_code": 429,
                    "detail": f"请求过于频繁，请稍后重试（{tier.window_human}）",
                    "retry_after_seconds": retry_after,
                    "path": request.url.path,
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._maybe_cleanup()
        return await call_next(request)


# ────────────────────────────────────────────────────────────────────
# Convenience: dependency-based rate limit check (for per-endpoint use)
# ────────────────────────────────────────────────────────────────────

_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Return the singleton rate limiter (set during app startup)."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter
