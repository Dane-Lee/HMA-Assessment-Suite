from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class SlidingWindowRateLimiter:
    """Small in-process limiter for credential and session write endpoints."""

    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._last_cleanup = monotonic()

    def allow(self, key: str) -> tuple[bool, int]:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            if now - self._last_cleanup >= self.window_seconds:
                stale_keys = [
                    stored_key
                    for stored_key, stored_attempts in self._attempts.items()
                    if not stored_attempts or stored_attempts[-1] <= cutoff
                ]
                for stored_key in stale_keys:
                    del self._attempts[stored_key]
                self._last_cleanup = now
            attempts = self._attempts[key]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - attempts[0])) + 1)
                return False, retry_after
            attempts.append(now)
            return True, 0
