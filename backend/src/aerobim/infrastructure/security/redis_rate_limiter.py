"""Redis-backed shared HTTP rate limiting (multi-replica)."""

from __future__ import annotations

import math

_REDIS_ALLOW_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
  return 0
end
return 1
"""


class RedisRateLimitBackend:
    """Fixed-window counter shared across app replicas via Redis.

    HD2-RL-01: this is a fixed window (INCR+EXPIRE). In-process
    ``InProcessRateLimitBackend`` is a sliding window. The same
    ``max_events`` can admit ~2× burst at a Redis window boundary.
    """

    def __init__(self, redis_url: str, *, key_prefix: str = "aerobim:ratelimit:") -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Redis rate limiter requires the 'redis' package; install enterprise extra"
            ) from exc
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = key_prefix
        self._script = self._redis.register_script(_REDIS_ALLOW_SCRIPT)

    def allow(self, *, bucket: str, key: str, max_events: int, window_seconds: float) -> bool:
        # HD2-RL-02: 0 = limiter off (by design in development). Pilot/production
        # reject <=0 at Settings boot.
        if max_events <= 0:
            return True
        ttl = max(1, int(math.ceil(window_seconds)))
        redis_key = f"{self._prefix}{bucket}:{key}"
        allowed = self._script(keys=[redis_key], args=[ttl, max_events])
        return bool(int(allowed or 0))


__all__ = ["RedisRateLimitBackend"]
