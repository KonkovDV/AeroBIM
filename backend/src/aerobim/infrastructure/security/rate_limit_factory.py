"""Rate-limit backend factory (infrastructure wiring)."""

from __future__ import annotations

import logging

from aerobim.core.security.rate_limit_backend import InProcessRateLimitBackend, RateLimitBackend

_logger = logging.getLogger(__name__)


def build_rate_limit_backend(
    redis_url: str | None,
    *,
    signoff_profile: str = "development",
    fail_closed: bool = False,
) -> RateLimitBackend:
    """Prefer Redis when configured; in-process only when not fail-closed."""

    hard_profile = signoff_profile in {"samolet_pilot", "production"}
    if not redis_url:
        if fail_closed:
            raise RuntimeError(
                "Redis rate limiter required outside development/test but "
                "AEROBIM_REDIS_URL is unset"
            )
        return InProcessRateLimitBackend()
    try:
        from aerobim.infrastructure.security.redis_rate_limiter import RedisRateLimitBackend

        return RedisRateLimitBackend(redis_url)
    except Exception as exc:
        if fail_closed or hard_profile:
            raise RuntimeError(
                "Redis rate limiter required for pilot/production but unavailable"
            ) from exc
        _logger.warning(
            "Redis rate limiter unavailable; using in-process limiter: %s",
            exc,
        )
        return InProcessRateLimitBackend()


__all__ = ["build_rate_limit_backend"]
