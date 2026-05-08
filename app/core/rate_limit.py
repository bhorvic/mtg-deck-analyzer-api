from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic


@dataclass(slots=True)
class SlidingWindowRateLimiter:
    max_requests: int
    window_seconds: int
    _requests: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _lock: Lock = field(default_factory=Lock)

    def allow(self, key: str) -> tuple[bool, float]:
        now = monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = max(1.0, self.window_seconds - (now - bucket[0]))
                return False, retry_after

            bucket.append(now)
            return True, 0.0

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()
